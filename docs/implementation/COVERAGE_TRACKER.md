# Coverage Tracker - Component Specification

## Overview

The coverage tracker implements AFL-style edge coverage tracking using a 64KB bitmap. It monitors code execution to provide feedback for coverage-guided fuzzing.

---

## Architecture

```
┌──────────────────────────────────────────┐
│        Coverage Tracker                  │
├──────────────────────────────────────────┤
│                                          │
│  ┌────────────────┐  ┌────────────────┐ │
│  │  Coverage Map  │  │  Virgin Map    │ │
│  │    (64KB)      │  │   (unseen)     │ │
│  └────────────────┘  └────────────────┘ │
│          │                   │           │
│          ▼                   ▼           │
│  ┌────────────────────────────────────┐ │
│  │     Coverage Comparator            │ │
│  └────────────────────────────────────┘ │
│          │                               │
│          ▼                               │
│  ┌────────────────────────────────────┐ │
│  │    Hit Count Classifier            │ │
│  └────────────────────────────────────┘ │
│                                          │
└──────────────────────────────────────────┘
```

---

## Class Design

### 1. CoverageMap

```python
from typing import Optional
import mmap
import os

class CoverageMap:
    """AFL-style 64KB coverage bitmap"""
    
    MAP_SIZE = 65536  # 64KB
    
    def __init__(self, shared_memory: bool = False):
        """
        Initialize coverage map
        
        Args:
            shared_memory: Use shared memory for IPC with target
        """
        if shared_memory:
            self.bitmap = self._create_shared_memory()
            self.shm_id = self._get_shm_id()
        else:
            self.bitmap = bytearray(self.MAP_SIZE)
            self.shm_id = None
        
        # Virgin map tracks unseen edges
        self.virgin_map = bytearray([0xFF] * self.MAP_SIZE)
        
        # Track previous location for edge calculation
        self.prev_location = 0
        
        # Statistics
        self.total_edges_found = 0
        self.edges_in_last_run = 0
    
    def reset(self):
        """Clear bitmap for new execution"""
        for i in range(self.MAP_SIZE):
            self.bitmap[i] = 0
        self.prev_location = 0
        self.edges_in_last_run = 0
    
    def record_edge(self, current_location: int):
        """
        Record edge execution (AFL-style)
        
        This is called from instrumented target code
        
        Args:
            current_location: Random ID assigned to current basic block
        """
        # Calculate edge ID via XOR
        edge_id = current_location ^ self.prev_location
        
        # Hash to bitmap index
        index = edge_id % self.MAP_SIZE
        
        # Increment hit counter (with saturation at 255)
        if self.bitmap[index] < 255:
            self.bitmap[index] += 1
        
        # Update previous location for next edge
        # Right shift to avoid reversing A->B to B->A
        self.prev_location = current_location >> 1
    
    def has_new_coverage(self) -> bool:
        """
        Check if current execution found new coverage
        
        Returns:
            True if new edges or hit count buckets discovered
        """
        found_new = False
        
        for i in range(self.MAP_SIZE):
            if self.bitmap[i]:
                # Check if this edge was virgin
                if self.virgin_map[i] & self.bitmap[i]:
                    found_new = True
                    self.edges_in_last_run += 1
        
        return found_new
    
    def update_virgin_map(self):
        """Mark current coverage as seen"""
        for i in range(self.MAP_SIZE):
            if self.bitmap[i]:
                # Clear bits that were hit
                self.virgin_map[i] &= ~self.bitmap[i]
                
        self.total_edges_found += self.edges_in_last_run
    
    def get_edge_count(self) -> int:
        """Count unique edges hit in current execution"""
        count = 0
        for byte_val in self.bitmap:
            if byte_val > 0:
                count += 1
        return count
    
    def classify_counts(self) -> bytearray:
        """
        Classify hit counts into buckets (AFL-style)
        
        Returns:
            Classified bitmap with bucketed hit counts
        """
        classified = bytearray(self.MAP_SIZE)
        
        for i in range(self.MAP_SIZE):
            classified[i] = self._count_class(self.bitmap[i])
        
        return classified
    
    def _count_class(self, count: int) -> int:
        """
        Classify hit count into bucket
        
        Buckets: 0, 1, 2, 3, 4-7, 8-15, 16-31, 32-127, 128+
        """
        if count == 0:
            return 0
        elif count == 1:
            return 1
        elif count == 2:
            return 2
        elif count == 3:
            return 3
        elif count <= 7:
            return 4
        elif count <= 15:
            return 5
        elif count <= 31:
            return 6
        elif count <= 127:
            return 7
        else:
            return 8
    
    def _create_shared_memory(self) -> mmap.mmap:
        """Create shared memory map for IPC"""
        # Create anonymous shared memory
        shm = mmap.mmap(-1, self.MAP_SIZE, mmap.MAP_SHARED)
        return shm
    
    def _get_shm_id(self) -> Optional[str]:
        """Get shared memory ID for passing to target"""
        # Implementation platform-specific
        # On Linux: use /dev/shm or shmget
        return None
```

---

### 2. CoverageComparator

```python
class CoverageComparator:
    """Compare coverage maps to detect new coverage"""
    
    @staticmethod
    def has_new_bits(virgin_map: bytearray, trace_bits: bytearray) -> bool:
        """
        Fast coverage comparison using 64-bit chunks
        
        Args:
            virgin_map: Bitmap of unseen edges
            trace_bits: Current execution coverage
            
        Returns:
            True if new coverage found
        """
        # Process 8 bytes at a time for speed
        virgin_64 = memoryview(virgin_map).cast('Q')  # u64 view
        trace_64 = memoryview(trace_bits).cast('Q')
        
        for i in range(len(virgin_64)):
            if trace_64[i] and (trace_64[i] & virgin_64[i]):
                return True
        
        return False
    
    @staticmethod
    def count_new_bits(virgin_map: bytearray, trace_bits: bytearray) -> int:
        """Count how many new bits were discovered"""
        new_bits = 0
        
        for i in range(len(virgin_map)):
            if trace_bits[i]:
                # Count set bits that are also set in virgin map
                new_bits += bin(trace_bits[i] & virgin_map[i]).count('1')
        
        return new_bits
    
    @staticmethod
    def compare_bitmaps(bitmap1: bytearray, bitmap2: bytearray) -> float:
        """
        Calculate similarity between two bitmaps
        
        Returns:
            Similarity score 0.0 (different) to 1.0 (identical)
        """
        matches = 0
        total = 0
        
        for i in range(len(bitmap1)):
            if bitmap1[i] == bitmap2[i]:
                matches += 1
            total += 1
        
        return matches / total if total > 0 else 0.0
```

---

### 3. CoverageAnalyzer

```python
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class CoverageStats:
    """Statistics about coverage"""
    total_edges: int
    unique_edges: int
    edge_density: float  # % of bitmap used
    max_hit_count: int
    avg_hit_count: float
    hot_edges: List[int]  # Most frequently hit edges

class CoverageAnalyzer:
    """Analyze coverage patterns"""
    
    def analyze(self, bitmap: bytearray) -> CoverageStats:
        """Generate statistics from coverage bitmap"""
        total_edges = 0
        unique_edges = 0
        max_hit = 0
        sum_hits = 0
        hot_edges = []
        
        for i, count in enumerate(bitmap):
            if count > 0:
                unique_edges += 1
                total_edges += count
                sum_hits += count
                max_hit = max(max_hit, count)
                
                # Track hot edges (hit > 100 times)
                if count > 100:
                    hot_edges.append(i)
        
        edge_density = (unique_edges / len(bitmap)) * 100
        avg_hit = sum_hits / unique_edges if unique_edges > 0 else 0
        
        return CoverageStats(
            total_edges=total_edges,
            unique_edges=unique_edges,
            edge_density=edge_density,
            max_hit_count=max_hit,
            avg_hit_count=avg_hit,
            hot_edges=hot_edges
        )
    
    def identify_interesting_inputs(self, corpus_coverage: Dict[str, bytearray]) -> List[str]:
        """
        Identify corpus inputs that provide unique coverage
        
        Args:
            corpus_coverage: Map of input_id -> coverage_bitmap
            
        Returns:
            List of interesting input IDs
        """
        virgin = bytearray([0xFF] * CoverageMap.MAP_SIZE)
        interesting = []
        
        for input_id, bitmap in corpus_coverage.items():
            # Check if this input provides new coverage
            has_new = False
            for i in range(len(bitmap)):
                if bitmap[i] and (bitmap[i] & virgin[i]):
                    has_new = True
                    break
            
            if has_new:
                interesting.append(input_id)
                # Update virgin map
                for i in range(len(bitmap)):
                    virgin[i] &= ~bitmap[i]
        
        return interesting
```

---

### 4. CoverageTracker (Main Interface)

```python
class CoverageTracker:
    """Main coverage tracking interface"""
    
    def __init__(self, shared_memory: bool = False):
        self.coverage_map = CoverageMap(shared_memory)
        self.comparator = CoverageComparator()
        self.analyzer = CoverageAnalyzer()
        
        # Track coverage history
        self.coverage_history: List[bytearray] = []
        self.run_count = 0
    
    def start_run(self):
        """Prepare for new execution"""
        self.coverage_map.reset()
        self.run_count += 1
    
    def end_run(self) -> bool:
        """
        Complete execution and check for new coverage
        
        Returns:
            True if new coverage was found
        """
        has_new = self.coverage_map.has_new_coverage()
        
        if has_new:
            # Save this coverage
            self.coverage_history.append(bytearray(self.coverage_map.bitmap))
            
            # Mark as seen
            self.coverage_map.update_virgin_map()
        
        return has_new
    
    def get_coverage_bitmap(self) -> bytearray:
        """Get current coverage bitmap"""
        return bytearray(self.coverage_map.bitmap)
    
    def get_stats(self) -> CoverageStats:
        """Get coverage statistics"""
        return self.analyzer.analyze(self.coverage_map.bitmap)
    
    def export_coverage(self, filepath: str):
        """Export coverage map to file"""
        with open(filepath, 'wb') as f:
            f.write(bytes(self.coverage_map.bitmap))
    
    def import_coverage(self, filepath: str):
        """Import coverage map from file"""
        with open(filepath, 'rb') as f:
            data = f.read()
            if len(data) == CoverageMap.MAP_SIZE:
                self.coverage_map.bitmap = bytearray(data)
```

---

## Integration with Target

### Option 1: Instrumented Target (Compile-Time)

```python
# Target code instrumentation
class InstrumentedTarget:
    def __init__(self, coverage_tracker: CoverageTracker):
        self.tracker = coverage_tracker
        self.prev_loc = 0
    
    def __enter_block(self, block_id: int):
        """Called at start of each basic block"""
        self.tracker.coverage_map.record_edge(block_id)
```

### Option 2: Python Coverage Module (Runtime)

```python
import coverage

class PythonCoverageAdapter:
    """Adapter for Python's coverage.py"""
    
    def __init__(self, coverage_tracker: CoverageTracker):
        self.tracker = coverage_tracker
        self.cov = coverage.Coverage()
    
    def start(self):
        self.cov.start()
    
    def stop(self):
        self.cov.stop()
        
        # Convert coverage.py data to bitmap
        data = self.cov.get_data()
        for filename in data.measured_files():
            arcs = data.arcs(filename) or []
            for arc in arcs:
                # Convert arc to edge ID
                edge_id = hash(arc) % CoverageMap.MAP_SIZE
                self.tracker.coverage_map.bitmap[edge_id] += 1
```

---

## Performance Targets

- **Edge Recording:** < 50ns per edge
- **Coverage Comparison:** < 1ms for full bitmap
- **Bitmap Reset:** < 100μs
- **Memory:** 128KB (64KB bitmap + 64KB virgin)

---

Status: Coverage tracker specification complete
