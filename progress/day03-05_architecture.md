# Days 3-5 - Architecture Refinement

**Phase:** Foundation  
**Focus:** Component specifications and system design

---

## Goals Completed

- Finalized mutation engine design
- Designed coverage tracking system
- Planned crash detection mechanisms
- Created detailed component specifications
- Defined protocol parser interfaces
- Documented fuzzing loop architecture
- Created component integration diagrams

---

## Architecture Specifications Created

### 1. Mutation Engine (MUTATION_ENGINE.md - 16KB)

**Components Designed:**
- `MutationEngine` - Main coordinator class
- `DeterministicMutator` - Systematic bit/byte flips, arithmetic
- `HavocMutator` - Random mutation stacking
- `DictionaryManager` - Protocol-aware keyword injection (HTTP/DNS/SMTP/SQL)
- `SpliceMutator` - Crossover mutations

**Key Design Decisions:**
- AFL-inspired deterministic stages
- Weighted mutation selection based on effectiveness
- Mutation tracking for adaptive strategy selection
- Protocol-aware dictionaries for targeted fuzzing

**Performance Targets:**
- Bit flip: < 1ms per mutation
- Havoc: < 5ms for 200 iterations
- Batch generation: 1000 mutations/sec

---

### 2. Coverage Tracker (COVERAGE_TRACKER.md - 14KB)

**Components Designed:**
- `CoverageMap` - 64KB AFL-style bitmap
- `CoverageComparator` - Fast 64-bit chunk comparison
- `CoverageAnalyzer` - Statistics and analysis
- `CoverageTracker` - Main interface

**Key Features:**
- Edge coverage tracking (XOR-based hashing)
- Hit count buckets: 0, 1, 2, 3, 4-7, 8-15, 16-31, 32-127, 128+
- Virgin map for unseen edges
- Shared memory support for IPC

**Implementation Details:**
```python
edge_id = current_location ^ previous_location
bitmap_index = edge_id % 65536
bitmap[bitmap_index]++
```

**Performance Targets:**
- Edge recording: < 50ns per edge
- Coverage comparison: < 1ms for full bitmap
- Memory: 128KB (bitmap + virgin map)

---

### 3. Crash Detector (CRASH_DETECTOR.md - 18KB)

**Components Designed:**
- `CrashDetector` - Main crash detection interface
- `SignalHandler` - Unix signal handling
- `SanitizerMonitor` - ASan/MSan/UBSan integration
- `CrashClassifier` - Exploitability analysis
- `CrashMinimizer` - Binary search minimization
- `CrashReporter` - JSON report generation

**Signal Coverage:**
- SIGSEGV (Segmentation Fault)
- SIGABRT (Abort)
- SIGILL (Illegal Instruction)
- SIGFPE (Floating Point Exception)
- SIGBUS (Bus Error)

**Sanitizer Integration:**
- AddressSanitizer detection
- MemorySanitizer detection
- Stack trace extraction
- Error type parsing

**Crash Minimization:**
- Binary search algorithm
- Chunk size reduction
- Signal preservation check
- Target: < 30 seconds per crash

---

### 4. Protocol Parsers (PROTOCOL_PARSERS.md - 19KB)

**Base Interface:**
- `ProtocolParser` - Abstract base class
- `parse()` - Raw bytes → structured message
- `generate()` - Template → raw bytes
- `mutate_field()` - Targeted field mutation

**Protocol Implementations:**

**HTTPParser:**
- Request line parsing (method, path, version)
- Header parsing
- Body extraction
- Field-level mutations

**DNSParser:**
- Header parsing (transaction ID, flags, counts)
- Query name encoding/decoding
- Query type/class handling
- Compression pointer support

**SMTPParser:**
- Command parsing
- Argument extraction
- Protocol validation

**BinaryProtocolParser:**
- Grammar-based parsing
- Field definition support
- Computed fields (length, checksum)
- uint8/uint16/uint32/bytes types

**Auto-Detection:**
- `ProtocolDetector` - Auto-detect protocol from data
- `ParserFactory` - Factory pattern for parser creation

---

### 5. Fuzzing Loop (FUZZING_LOOP.md - 16KB)

**Main Algorithm:**
```
1. SELECT INPUT (Queue Scheduler)
2. MUTATE (Mutation Engine)
3. EXECUTE TARGET (Crash Detector)
4. COLLECT FEEDBACK (Coverage Tracker)
5. PROCESS RESULTS (Crashes/Coverage)
6. UPDATE STATS
7. REPEAT
```

**Queue Scheduling:**
- Weighted selection algorithm
- Prioritize by coverage score
- Favor smaller inputs
- Favor less-executed entries
- Favor favored inputs (2x weight)

**Corpus Management:**
- Duplicate detection (MD5 hash)
- Automatic corpus addition on new coverage
- Seed loading from directory

**Statistics Tracking:**
- Total executions
- Total edges found
- Unique crashes
- Executions per second
- Time since last coverage/crash

**Configuration:**
```python
@dataclass
class FuzzingConfig:
    target_cmd: List[str]
    seed_corpus: Path
    max_time: Optional[int]
    max_execs: Optional[int]
    timeout_ms: int = 5000
    enable_asan: bool = True
    minimize_crashes: bool = True
```

---

### 6. Component Integration (COMPONENT_INTEGRATION.md - 25KB)

**System Architecture:**
```
CLI → Fuzzing Loop → Components
         ├─ Queue Scheduler
         ├─ Mutation Engine
         ├─ Protocol Parsers
         ├─ Coverage Tracker
         └─ Crash Detector
```

**Data Flow:**
```
Seeds → Corpus → Queue → Mutate → Execute → Analyze
                   ↑                           │
                   └───── New Coverage ────────┘
```

**Component Interactions:**
- FuzzingLoop coordinates all components
- Protocol parsers feed mutation engine
- Coverage tracker provides feedback
- Crash detector monitors execution
- Corpus manager handles interesting inputs

**Communication Patterns:**
- Shared memory for coverage bitmap
- Process forking for target execution
- JSON for crash reports
- Statistics aggregation

---

## Key Design Decisions

### 1. AFL-Style Coverage
- Chosen 64KB bitmap (L2 cache optimized)
- Edge coverage over basic block coverage
- Hit count buckets for loop depth detection
- XOR-based edge hashing

### 2. Modular Architecture
- Clear component boundaries
- Abstract base classes for extensibility
- Protocol-agnostic fuzzing loop
- Plugin architecture for new protocols

### 3. Performance First
- Fast bitmap comparison (64-bit chunks)
- Efficient mutation strategies
- Minimal overhead on execution path
- Parallel fuzzing support

### 4. Production Ready
- Comprehensive error handling
- Detailed crash reports
- Exploitability analysis
- Crash minimization

---

## Research Applied

**From mutation_strategies.md:**
- Implemented deterministic bit/byte flips
- Added havoc mutation stacking
- Dictionary-based protocol fuzzing
- Splice mutations for diversity

**From crash_detection.md:**
- Signal-based crash detection
- Sanitizer integration (ASan/MSan)
- Stack trace parsing
- Crash deduplication

**From afl_bitmap.md:**
- 64KB bitmap implementation
- Edge hashing algorithm
- Hit count buckets
- Virgin map tracking

**From protocol_vulnerabilities.md:**
- HTTP header injection patterns
- DNS compression attacks
- SMTP command injection
- Binary protocol fuzzing

---

## Component Specifications Summary

| Component | Spec File | Size | Classes | Key Features |
|-----------|-----------|------|---------|--------------|
| Mutation Engine | MUTATION_ENGINE.md | 16KB | 5 | Deterministic, Havoc, Dictionary, Splice |
| Coverage Tracker | COVERAGE_TRACKER.md | 14KB | 4 | 64KB bitmap, Hit buckets, Edge tracking |
| Crash Detector | CRASH_DETECTOR.md | 18KB | 6 | Signals, Sanitizers, Minimization |
| Protocol Parsers | PROTOCOL_PARSERS.md | 19KB | 6 | HTTP, DNS, SMTP, Binary, Auto-detect |
| Fuzzing Loop | FUZZING_LOOP.md | 16KB | 5 | Main loop, Queue, Corpus, Stats |
| Integration | COMPONENT_INTEGRATION.md | 25KB | N/A | Architecture diagrams, Data flow |

**Total:** 108KB of production-ready specifications

---

## Next Steps

**Days 6-7: Development Environment**
- Set up Python package structure
- Configure pytest framework
- Set up linting (ruff, black, mypy)
- Create pre-commit hooks
- Add CI/CD configuration
- Create initial package files

**Days 8-14: Implementation**
- Begin coding mutation engine
- Implement coverage tracker
- Build crash detector
- Create fuzzing loop
- Integration testing

---

## Lessons Learned

1. **Modular design is critical** - Each component has clear boundaries and responsibilities
2. **Performance matters** - 64-bit chunks for fast bitmap comparison
3. **Protocol awareness helps** - Structure-aware mutations find more bugs
4. **AFL principles work** - Edge coverage and hit count buckets are proven
5. **Production quality from start** - Error handling and reporting built-in

---

## Code Changes

**Files Created:**
- docs/implementation/MUTATION_ENGINE.md
- docs/implementation/COVERAGE_TRACKER.md
- docs/implementation/CRASH_DETECTOR.md
- docs/implementation/PROTOCOL_PARSERS.md
- docs/implementation/FUZZING_LOOP.md
- docs/architecture/COMPONENT_INTEGRATION.md

**Architecture Complete:**
- All core components specified
- Ready for implementation
- Clear interfaces defined
- Performance targets set

---

Status: Architecture refinement complete, ready for development environment setup
