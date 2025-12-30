# Day 14: Fuzzing Loop Integration - Implementation Plan

## Overview
Implement the main fuzzing coordinator that integrates all components (mutation, coverage, crash detection) into a cohesive fuzzing loop.

## Components to Implement

### 1. CorpusManager
**Purpose:** Manage fuzzing corpus (seeds and interesting inputs)

**Features:**
- Add/remove seeds
- Track interesting inputs (new coverage)
- Persist corpus to disk
- Load corpus from disk
- Get random seed for mutation

**File:** `src/protocrash/fuzzing_engine/corpus.py`

---

### 2. QueueScheduler
**Purpose:** Prioritize which inputs to fuzz next

**Features:**
- Queue management with priorities
- Favor inputs with new coverage
- Favor smaller inputs
- Track execution count per input
- Energy assignment (AFL-style)

**File:** `src/protocrash/fuzzing_engine/scheduler.py`

---

### 3. FuzzingStats
**Purpose:** Track and display fuzzing statistics

**Features:**
- Execution count
- Crash count
- Coverage metrics
- Executions per second
- Time elapsed
- Corpus size
- Queue depth

**File:** `src/protocrash/fuzzing_engine/stats.py`

---

### 4. FuzzingCoordinator
**Purpose:** Main fuzzing loop integrating all components

**Features:**
- Initialize all components
- Main fuzzing loop
- Input selection
- Mutation
- Execution
- Coverage tracking
- Crash detection
- Corpus updates
- Statistics updates

**File:** `src/protocrash/fuzzing_engine/coordinator.py`

---

## Integration Flow

```
┌─────────────────────────────────────┐
│    FuzzingCoordinator (Main Loop)   │
└─────────────────────────────────────┘
            │
            ├─► CorpusManager
            │   └─► Get seed
            │
            ├─► QueueScheduler
            │   └─► Prioritize inputs
            │
            ├─► MutationEngine
            │   └─► Mutate input
            │
            ├─► CoverageTracker
            │   └─► Track coverage
            │
            ├─► CrashDetector
            │   └─► Detect crashes
            │
            └─► FuzzingStats
                └─► Update metrics
```

---

## Implementation Order

1. **CorpusManager** - Foundation for seed management
2. **QueueScheduler** - Prioritization logic
3. **FuzzingStats** - Metrics tracking
4. **FuzzingCoordinator** - Main integration
5. **Tests** - Comprehensive unit and integration tests

---

## Design Decisions

### Corpus Management
- Store as files in `corpus/` directory
- Each input = separate file
- Metadata in JSON sidecar files
- SHA256 hash for deduplication

### Queue Scheduling  
- Priority queue with multiple factors
- Energy based on:
  - Coverage contribution
  - Input size
  - Execution count
- AFL-style power scheduling

### Statistics
- Real-time updates
- Periodic display (every N seconds)
- JSON export for analysis

### Coordinator
- Single-threaded initially (Day 24-25 adds parallelism)
- Configurable timeout
- Signal handling for graceful shutdown
- Checkpoint/resume support

---

## Testing Strategy

- Unit tests for each component
- Integration tests for full loop
- Mock target for deterministic testing
- Coverage target: 95%+

---

## Success Criteria

- [ ] All 4 components implemented
- [ ] Full fuzzing loop working
- [ ] 95%+ test coverage
- [ ] Integration test fuzzing sample target
- [ ] Stats display working

---

**Start Time:** 2025-12-27  
**Target:** Complete Day 14 implementation
