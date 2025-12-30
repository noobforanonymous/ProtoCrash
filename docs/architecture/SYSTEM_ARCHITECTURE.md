# ProtoCrash - System Architecture

## ARCHITECTURE: High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        ProtoCrash                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │     CLI      │───▶│    Fuzzing   │───▶│   Target     │  │
│  │  Interface   │    │    Engine    │    │  Executor    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Input       │    │  Mutation    │    │  Coverage    │  │
│  │  Corpus      │    │  Engine      │    │  Tracker     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Protocol    │    │   Queue      │    │   Crash      │  │
│  │  Parsers     │    │  Scheduler   │    │  Detector    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. CLI Interface Layer
**Purpose:** User interaction and configuration

**Components:**
- **Main CLI:** Command-line interface for fuzzing operations
- **Config Manager:** Load and validate fuzzing configuration
- **Stats Display:** Real-time fuzzing statistics and progress

**Tech Stack:**
- CLI: Python `click`
- Display: `rich` for formatting
- Config: YAML/JSON parsing

---

### 2. Fuzzing Engine
**Purpose:** Core fuzzing logic and orchestration

**Responsibilities:**
- Coordinate fuzzing loop
- Manage corpus and queue
- Track coverage feedback
- Schedule test case execution
- Detect interesting inputs

**Algorithm:**
```
while fuzzing_active:
    1. Select input from queue (weighted by coverage)
    2. Mutate input using mutation strategies
    3. Execute target with mutated input
    4. Collect coverage feedback
    5. If new coverage found:
        - Add to corpus
        - Mark as interesting
    6. If crash detected:
        - Save crash input
        - Triage and report
    7. Update statistics
```

**Tech Stack:**
- Pure Python implementation
- Coverage-guided scheduling
- Feedback-driven mutations

---

### 3. Mutation Engine
**Purpose:** Generate test cases through intelligent mutations

**Mutation Strategies:**
- **Bit Flips:** Flip individual bits
- **Byte Flips:** Flip sequences of bytes
- **Arithmetic:** Add/subtract small integers
- **Interesting Values:** Inject known edge cases (0, -1, MAX_INT)
- **Block Operations:** Delete, insert, duplicate blocks
- **Dictionary-Based:** Inject common protocol keywords
- **Cross-Over:** Splice two inputs together
- **Structure-Aware:** Respect protocol grammar

**Implementation:**
```python
class MutationEngine:
    def mutate(self, input_data: bytes, strategy: str) -> bytes:
        # Apply selected mutation strategy
        # Return mutated input
```

**Tech Stack:**
- NumPy for efficient byte operations
- Custom mutation algorithms
- Grammar-based mutations for structured protocols

---

### 4. Coverage Tracker
**Purpose:** Monitor code coverage for feedback-driven fuzzing

**Features:**
- **Edge Coverage:** Track branch transitions (A→B)
- **Hit Counts:** Record execution frequency (buckets: 1, 2, 3, 4-7, 8-15, 16+)
- **Coverage Map:** Maintain bitmap of executed edges
- **New Path Detection:** Identify inputs that trigger new coverage

**Implementation:**
```python
class CoverageTracker:
    coverage_map: Dict[int, int]  # edge_id -> hit_count
    
    def record_edge(self, edge_id: int):
        # Record edge execution
        # Update hit count bucket
    
    def has_new_coverage(self, previous_map) -> bool:
        # Compare with previous coverage
        # Return True if new edges or hit counts
```

**Tech Stack:**
- Shared memory for coverage map
- Fast bitmap comparison
- Coverage visualization

---

### 5. Target Executor
**Purpose:** Execute target application with test inputs

**Features:**
- **Process Management:** Spawn target process
- **Input Delivery:** Feed test case via stdin/network/file
- **Timeout Handling:** Kill hangs after timeout
- **Resource Limits:** CPU, memory, file descriptor limits
- **Crash Detection:** Monitor signals (SIGSEGV, SIGABRT, SIGILL)
- **Output Capture:** Collect stdout/stderr

**Implementation:**
```python
class TargetExecutor:
    def execute(self, input_data: bytes, timeout: int) -> ExecutionResult:
        # Spawn target process
        # Deliver input
        # Monitor execution
        # Detect crash/hang
        # Collect coverage
        # Return ExecutionResult
```

**Tech Stack:**
- `subprocess` for process management
- `pwntools` for advanced process interaction
- Signal handling for crash detection

---

### 6. Protocol Parsers
**Purpose:** Understand and generate protocol-specific inputs

**Supported Protocols:**
- **HTTP:** Request/response parsing and generation
- **DNS:** Query/response manipulation
- **SMTP:** Command/response handling
- **Custom Binary:** Grammar-based protocol definition

**Parser Interface:**
```python
class ProtocolParser:
    def parse(self, data: bytes) -> ProtocolMessage:
        # Parse raw bytes into protocol structure
    
    def generate(self, template: dict) -> bytes:
        # Generate valid protocol message
    
    def mutate_field(self, message: ProtocolMessage, field: str) -> bytes:
        # Mutate specific protocol field
```

**Tech Stack:**
- Protocol-specific libraries (scapy, dpkt)
- Custom parsers for binary formats
- Grammar definitions for extensibility

---

### 7. Queue Scheduler
**Purpose:** Prioritize test cases for execution

**Scheduling Strategies:**
- **Favor Small:** Prefer shorter inputs
- **Favor Recent:** Prioritize recently added inputs
- **Favor Coverage:** Weight by coverage density
- **Random:** Occasionally select random inputs

**Implementation:**
```python
class QueueScheduler:
    queue: List[QueueEntry]
    
    def add(self, entry: QueueEntry):
        # Add entry with priority
    
    def next(self) -> QueueEntry:
        # Select next input based on strategy
```

---

### 8. Crash Detector & Analyzer
**Purpose:** Detect and triage crashes

**Detection:**
- Signal monitoring (SIGSEGV, SIGABRT, SIGILL, SIGFPE)
- Timeout detection (hangs)
- Memory sanitizer integration (ASan, MSan)
- Exit code analysis

**Triage:**
- **Crash Bucketing:** Group similar crashes
- **Stack Trace:** Parse and deduplicate
- **Exploitability:** Classify crash severity
- **Minimization:** Reduce input to minimal crash case

**Tech Stack:**
- GDB for crash analysis
- Stack trace parsing
- Crash deduplication algorithms

---

## Data Flow

### Fuzzing Cycle
```
1. Corpus Input
   ↓
2. Queue Scheduler (select input)
   ↓
3. Mutation Engine (mutate)
   ↓
4. Protocol Parser (validate/fix)
   ↓
5. Target Executor (run)
   ↓
6. Coverage Tracker (analyze)
   ↓
7. Decision:
   - New Coverage? → Add to Corpus
   - Crash? → Save to Crashes
   - Nothing New? → Discard
   ↓
8. Repeat
```

---

## Data Storage

### Directory Structure
```
ProtoCrash/
├── corpus/           # Input corpus
│   ├── initial/      # Seed inputs
│   └── queue/        # Generated interesting inputs
├── crashes/          # Crash reproducers
│   ├── unique/       # Unique crashes
│   └── duplicates/   # Duplicate crashes
├── data/
│   ├── raw/          # Raw protocol samples
│   └── processed/    # Parsed protocol data
├── coverage/         # Coverage maps
└── logs/             # Fuzzing logs
```

### File Formats
- **Corpus:** Raw binary files
- **Crashes:** Binary + metadata (stack trace, signal)
- **Coverage:** Binary bitmap
- **Logs:** JSON for structured data

---

## SECURITY: Security Considerations

### Target Isolation
- Run targets in sandboxed environment
- Use namespaces/containers for isolation
- Limit network access
- Restrict file system access

### Resource Limits
- CPU time limits
- Memory limits
- File descriptor limits
- Process limits

### Safety Features
- Automatic timeout on hangs
- Crash recovery
- Resource cleanup

---

## Performance Targets

- **Execution Rate:** 100-1000 execs/sec (depending on target)
- **Startup Time:** Less than 5 seconds
- **Memory Usage:** Less than 1GB (excluding target)
- **Crash Detection:** Less than 100ms overhead
- **Coverage Tracking:** Less than 10% overhead

---

## Scalability

### Phase 1 (MVP)
- Single process fuzzing
- Local corpus
- Basic coverage tracking

### Phase 2 (Enhanced)
- Multi-core parallel fuzzing
- Shared corpus synchronization
- Advanced coverage metrics

### Phase 3 (Distributed)
- Multiple machine coordination
- Centralized corpus management
- Distributed crash deduplication

---

Status: Architecture complete, ready for implementation
