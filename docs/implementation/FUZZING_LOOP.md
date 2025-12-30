# Fuzzing Loop Architecture - Complete Specification

## Overview

The fuzzing loop is the core orchestrator that coordinates all components to perform coverage-guided fuzzing. This document describes the main fuzzing algorithm, queue management, and component integration.

---

## Main Fuzzing Algorithm

### Core Loop

```python
class FuzzingLoop:
    """Main fuzzing coordinator"""
    
    def __init__(self, config: FuzzingConfig):
        self.config = config
        
        # Initialize components
        self.mutation_engine = MutationEngine()
        self.coverage_tracker = CoverageTracker()
        self.crash_detector = CrashDetector()
        self.corpus_manager = CorpusManager()
        self.queue_scheduler = QueueScheduler()
        
        # Statistics
        self.stats = FuzzingStats()
    
    def fuzz(self, target_cmd: List[str], seed_corpus: Path):
        """
        Main fuzzing loop
        
        Args:
            target_cmd: Command to execute target
            seed_corpus: Directory with seed inputs
        """
        # Load seed corpus
        self.corpus_manager.load_seeds(seed_corpus)
        self.queue_scheduler.initialize(self.corpus_manager.get_corpus())
        
        print(f"[+] Loaded {len(self.corpus_manager)} seeds")
        print(f"[*] Starting fuzzing loop...")
        
        while not self._should_stop():
            # === STAGE 1: SELECT INPUT ===
            current_input = self.queue_scheduler.next()
            if not current_input:
                break
            
            self.stats.increment_exec()
            
            # === STAGE 2: MUTATE ===
            mutated_input = self.mutation_engine.mutate(
                current_input.data,
                strategy='auto'
            )
            
            # === STAGE 3: EXECUTE TARGET ===
            self.coverage_tracker.start_run()
            
            crash_info = self.crash_detector.execute_and_detect(
                target_cmd,
                mutated_input
            )
            
            has_new_coverage = self.coverage_tracker.end_run()
            
            # === STAGE 4: PROCESS RESULTS ===
            if crash_info.crashed:
                self._handle_crash(crash_info, mutated_input)
            
            if has_new_coverage:
                self._handle_new_coverage(mutated_input)
            
            # === STAGE 5: UPDATE STATS ===
            self._update_stats()
        
        print(f"\n[*] Fuzzing complete!")
        print(f"    Total executions: {self.stats.total_execs}")
        print(f"    Crashes found: {self.stats.unique_crashes}")
        print(f"    Coverage: {self.stats.total_edges} edges")
    
    def _should_stop(self) -> bool:
        """Check if fuzzing should stop"""
        if self.config.max_time and self.stats.elapsed_time() > self.config.max_time:
            return True
        
        if self.config.max_execs and self.stats.total_execs >= self.config.max_execs:
            return True
        
        return False
    
    def _handle_crash(self, crash: CrashInfo, input_data: bytes):
        """Handle crash discovery"""
        # Classify crash
        classifier = CrashClassifier()
        crash_hash = classifier.generate_crash_hash(crash)
        
        # Check if unique
        if crash_hash not in self.stats.crash_hashes:
            self.stats.crash_hashes.add(crash_hash)
            self.stats.unique_crashes += 1
            
            # Save crash
            crash_path = self.config.crash_dir / f"crash_{crash_hash}.input"
            crash_path.write_bytes(input_data)
            
            print(f"[!] New crash: {crash.crash_type.value} ({crash_hash[:8]})")
            
            # Minimize crash (optional)
            if self.config.minimize_crashes:
                minimizer = CrashMinimizer(self.crash_detector)
                minimized = minimizer.minimize(self.config.target_cmd, input_data)
                print(f"    Minimized: {len(input_data)} -> {len(minimized)} bytes")
    
    def _handle_new_coverage(self, input_data: bytes):
        """Handle new coverage discovery"""
        # Add to corpus
        corpus_entry = self.corpus_manager.add(input_data)
        
        # Add to queue
        self.queue_scheduler.add(corpus_entry)
        
        self.stats.total_edges = self.coverage_tracker.coverage_map.total_edges_found
        
        print(f"[+] New coverage: {self.stats.total_edges} total edges")
    
    def _update_stats(self):
        """Update and display statistics"""
        if self.stats.total_execs % 100 == 0:
            self._display_stats()
    
    def _display_stats(self):
        """Display fuzzing statistics"""
        print(f"\r[*] execs: {self.stats.total_execs} | "
              f"crashes: {self.stats.unique_crashes} | "
              f"edges: {self.stats.total_edges} | "
              f"corpus: {len(self.corpus_manager)} | "
              f"speed: {self.stats.execs_per_sec():.1f}/sec", end='')
```

---

## Queue Scheduling Algorithm

### Queue Entry

```python
@dataclass
class QueueEntry:
    """Entry in fuzzing queue"""
    id: str
    data: bytes
    depth: int  # Mutation depth from seed
    coverage_score: float  # How much coverage it provides
    exec_count: int  # Times executed
    last_exec_time: float
    favored: bool  # Prioritize this input
```

### Scheduler Strategies

```python
class QueueScheduler:
    """Intelligent queue scheduling"""
    
    def __init__(self):
        self.queue: List[QueueEntry] = []
        self.current_index = 0
    
    def initialize(self, corpus: List[bytes]):
        """Initialize queue from corpus"""
        for i, data in enumerate(corpus):
            entry = QueueEntry(
                id=f"seed_{i}",
                data=data,
                depth=0,
                coverage_score=0.0,
                exec_count=0,
                last_exec_time=0.0,
                favored=True  # Seeds are favored
            )
            self.queue.append(entry)
    
    def next(self) -> QueueEntry:
        """Select next input from queue"""
        if not self.queue:
            return None
        
        # Strategy: Weighted selection
        entry = self._weighted_select()
        entry.exec_count += 1
        entry.last_exec_time = time.time()
        
        return entry
    
    def add(self, entry: QueueEntry):
        """Add new entry to queue"""
        self.queue.append(entry)
    
    def _weighted_select(self) -> QueueEntry:
        """Select entry with weighted probability"""
        weights = []
        
        for entry in self.queue:
            weight = 1.0
            
            # Favor entries with high coverage
            weight *= (1.0 + entry.coverage_score)
            
            # Favor smaller inputs
            weight *= (1.0 / (1.0 + len(entry.data) / 1000.0))
            
            # Favor less-executed entries
            weight *= (1.0 / (1.0 + entry.exec_count / 10.0))
            
            # Favor favored entries
            if entry.favored:
                weight *= 2.0
            
            weights.append(weight)
        
        # Weighted random selection
        total = sum(weights)
        r = random.uniform(0, total)
        
        cumsum = 0.0
        for entry, weight in zip(self.queue, weights):
            cumsum += weight
            if r <= cumsum:
                return entry
        
        return self.queue[-1]
```

---

## Corpus Management

```python
class CorpusManager:
    """Manage fuzzing corpus"""
    
    def __init__(self):
        self.corpus: List[bytes] = []
        self.corpus_hashes: Set[str] = set()
    
    def load_seeds(self, seed_dir: Path):
        """Load seed corpus from directory"""
        for seed_file in seed_dir.glob("*"):
            if seed_file.is_file():
                data = seed_file.read_bytes()
                self.add(data)
    
    def add(self, data: bytes) -> QueueEntry:
        """Add input to corpus (if unique)"""
        data_hash = hashlib.md5(data).hexdigest()
        
        if data_hash in self.corpus_hashes:
            return None  # Duplicate
        
        self.corpus.append(data)
        self.corpus_hashes.add(data_hash)
        
        return QueueEntry(
            id=f"corpus_{len(self.corpus)}",
            data=data,
            depth=0,
            coverage_score=0.0,
            exec_count=0,
            last_exec_time=0.0,
            favored=False
        )
    
    def get_corpus(self) -> List[bytes]:
        """Get all corpus inputs"""
        return self.corpus
    
    def __len__(self):
        return len(self.corpus)
```

---

## Statistics Tracking

```python
import time

class FuzzingStats:
    """Track fuzzing statistics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.total_execs = 0
        self.total_edges = 0
        self.unique_crashes = 0
        self.crash_hashes: Set[str] = set()
        
        self.last_coverage_time = time.time()
        self.last_crash_time = time.time()
    
    def increment_exec(self):
        """Increment execution count"""
        self.total_execs += 1
    
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time
    
    def execs_per_sec(self) -> float:
        """Calculate executions per second"""
        elapsed = self.elapsed_time()
        if elapsed == 0:
            return 0.0
        return self.total_execs / elapsed
    
    def time_since_coverage(self) -> float:
        """Time since last new coverage"""
        return time.time() - self.last_coverage_time
    
    def time_since_crash(self) -> float:
        """Time since last crash"""
        return time.time() - self.last_crash_time
```

---

## Configuration

```python
@dataclass
class FuzzingConfig:
    """Fuzzing configuration"""
    target_cmd: List[str]
    seed_corpus: Path
    crash_dir: Path = Path("./crashes")
    corpus_dir: Path = Path("./corpus")
    
    # Time limits
    max_time: Optional[int] = None  # seconds
    max_execs: Optional[int] = None
    
    # Execution
    timeout_ms: int = 5000
    enable_asan: bool = True
    
    # Mutation
    deterministic_stage: bool = True
    havoc_stage: bool = True
    splice_stage: bool = True
    
    # Features
    minimize_crashes: bool = True
    parallel_workers: int = 1
```

---

## Integration Flow

### Complete Execution Cycle

```
┌─────────────────────────────────────────────────────────┐
│                   FUZZING LOOP                           │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 1. SELECT INPUT                                          │
│    - Queue Scheduler picks next input                    │
│    - Weighted by coverage, size, exec count              │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 2. MUTATE                                                │
│    - Mutation Engine applies strategy                    │
│    - Deterministic / Havoc / Dictionary / Splice         │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 3. EXECUTE TARGET                                        │
│    - Coverage Tracker resets                             │
│    - Crash Detector launches target                      │
│    - Target runs with mutated input                      │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 4. COLLECT FEEDBACK                                      │
│    - Coverage Tracker checks for new edges               │
│    - Crash Detector checks for signals                   │
└─────────────────────────────────────────────────────────┘
                         │
                ┌────────┴────────┐
                ▼                 ▼
        ┌──────────────┐  ┌──────────────┐
        │   CRASHED?   │  │NEW COVERAGE? │
        └──────────────┘  └──────────────┘
                │                 │
                ▼                 ▼
        ┌──────────────┐  ┌──────────────┐
        │ Save Crash   │  │ Add to Corpus│
        │ Minimize     │  │ Add to Queue │
        │ Triage       │  │ Update Stats │
        └──────────────┘  └──────────────┘
                │                 │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │  Update Stats   │
                │  Display Info   │
                └─────────────────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ Continue Loop │
                 └───────────────┘
```

---

## Performance Optimizations

### 1. Batch Execution

```python
def fuzz_batch(self, inputs: List[bytes], target_cmd: List[str]) -> List[CrashInfo]:
    """Execute multiple inputs in batch"""
    results = []
    
    for input_data in inputs:
        self.coverage_tracker.start_run()
        result = self.crash_detector.execute_and_detect(target_cmd, input_data)
        self.coverage_tracker.end_run()
        results.append(result)
    
    return results
```

### 2. Parallel Fuzzing

```python
from multiprocessing import Pool

class ParallelFuzzer:
    """Run multiple fuzzing instances in parallel"""
    
    def __init__(self, config: FuzzingConfig, num_workers: int):
        self.config = config
        self.num_workers = num_workers
    
    def fuzz_parallel(self):
        """Run parallel fuzzing instances"""
        with Pool(self.num_workers) as pool:
            pool.map(self._worker_fuzz, range(self.num_workers))
    
    def _worker_fuzz(self, worker_id: int):
        """Fuzzing worker process"""
        fuzzer = FuzzingLoop(self.config)
        fuzzer.fuzz(
            self.config.target_cmd,
            self.config.seed_corpus
        )
```

---

Status: Fuzzing loop architecture specification complete
