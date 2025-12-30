# Component Integration - System Diagrams

## Overall System Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            PROTOCRASH FUZZER                                │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                       CLI INTERFACE                                   │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐ │ │
│  │  │ fuzz       │  │ analyze    │  │ corpus     │  │ monitor        │ │ │
│  │  │ command    │  │ command    │  │ command    │  │ command        │ │ │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                  │                                         │
│                                  ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                       FUZZING LOOP                                    │ │
│  │  ┌────────────────────────────────────────────────────────────────┐  │ │
│  │  │  Queue Scheduler → Mutation Engine → Target Executor →        │  │ │
│  │  │  Coverage Tracker → Crash Detector → Corpus Manager           │  │ │
│  │  └────────────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│         │                    │                    │                       │
│         ▼                    ▼                    ▼                       │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐              │
│  │  Protocol   │      │  Mutation   │      │  Coverage   │              │
│  │  Parsers    │      │  Engine     │      │  Tracker    │              │
│  │             │      │             │      │             │              │
│  │ HTTP        │      │ Deterministic     │ 64KB Bitmap │              │
│  │ DNS         │      │ Havoc       │      │ Hit Counts  │              │
│  │ SMTP        │      │ Dictionary  │      │ Virgin Map  │              │
│  │ Binary      │      │ Splice      │      └─────────────┘              │
│  └─────────────┘      └─────────────┘                                    │
│         │                    │                                            │
│         └────────────────────┴──────────────┐                            │
│                                              ▼                            │
│                                       ┌─────────────┐                     │
│                                       │   Crash     │                     │
│                                       │   Detector  │                     │
│                                       │             │                     │
│                                       │ Signals     │                     │
│                                       │ Sanitizers  │                     │
│                                       │ Classifier  │                     │
│                                       │ Minimizer   │                     │
│                                       └─────────────┘                     │
│                                              │                            │
│                                              ▼                            │
│                                       ┌─────────────┐                     │
│                                       │   Output    │                     │
│                                       │             │                     │
│                                       │ Crashes/    │                     │
│                                       │ Corpus/     │                     │
│                                       │ Stats       │                     │
│                                       └─────────────┘                     │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Architecture

```
INPUT SEEDS
    │
    ▼
┌────────────────┐
│ Corpus Manager │ ◄─────────────────┐
└────────────────┘                   │
    │                                │
    ▼                                │
┌────────────────┐                   │
│Queue Scheduler │                   │
└────────────────┘                   │
    │                                │
    │  SELECT                        │
    ▼                                │
┌────────────────┐                   │
│ Current Input  │                   │
└────────────────┘                   │
    │                                │
    │  MUTATE                        │
    ▼                                │
┌────────────────┐                   │
│Mutation Engine │                   │
│  ├─ Protocol   │                   │
│  │  Parser?    │                   │
│  └─ Mutators   │                   │
└────────────────┘                   │
    │                                │
    │  MUTATED INPUT                 │
    ▼                                │
┌────────────────┐                   │
│Target Executor │                   │
│  ├─ Spawn      │                   │
│  ├─ Feed Input │                   │
│  └─ Monitor    │                   │
└────────────────┘                   │
    │                                │
    ├── COVERAGE ──────┐             │
    │                  ▼             │
    │           ┌────────────────┐   │
    │           │Coverage Tracker│   │
    │           │  ├─ Record     │   │
    │           │  ├─ Compare    │   │
    │           │  └─ Classify   │   │
    │           └────────────────┘   │
    │                  │             │
    │                  │ NEW?        │
    │                  └─────────────┤
    │                                │
    └── SIGNALS ───────┐             │
                      ▼             │
               ┌────────────────┐   │
               │Crash Detector  │   │
               │  ├─ Signals    │   │
               │  ├─ Sanitizers │   │
               │  ├─ Classify   │   │
               │  └─ Minimize   │   │
               └────────────────┘   │
                      │             │
                      │ CRASH?      │
                      ▼             │
               ┌────────────────┐   │
               │  Save Crash    │   │
               └────────────────┘   │
                                    │
            ADD TO CORPUS ──────────┘
```

---

## Component Interaction Diagram

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│  FuzzingLoop    │────────▶│QueueScheduler   │────────▶│  CorpusManager  │
│                 │         │                 │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
        │                           │
        │ select()                  │ next()
        ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │
│ MutationEngine  │◄────────│  QueueEntry     │
│                 │         │                 │
└─────────────────┘         └─────────────────┘
        │
        │ mutate()
        ▼
┌─────────────────┐         ┌─────────────────┐
│                 │────────▶│                 │
│ ProtocolParser  │         │ Deterministic   │
│                 │         │ Havoc           │
└─────────────────┘         │ Dictionary      │
        │                   │ Splice          │
        │ parse()           └─────────────────┘
        │ generate()
        ▼
┌─────────────────┐
│                 │
│ Mutated Input   │
│                 │
└─────────────────┘
        │
        │ execute()
        ▼
┌─────────────────┐         ┌─────────────────┐
│                 │────────▶│                 │
│ CrashDetector   │         │CoverageTracker  │
│                 │         │                 │
└─────────────────┘         └─────────────────┘
        │                           │
        │ detect()                  │ check_new()
        ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │
│   CrashInfo     │         │  CoverageMap    │
│                 │         │                 │
└─────────────────┘         └─────────────────┘
        │                           │
        │ if crashed                │ if new
        ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │
│CrashClassifier  │         │   Add to        │
│CrashMinimizer   │         │   Corpus        │
│CrashReporter    │         │                 │
└─────────────────┘         └─────────────────┘
```

---

## Class Relationship Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    FuzzingLoop                           │
├──────────────────────────────────────────────────────────┤
│ - config: FuzzingConfig                                  │
│ - mutation_engine: MutationEngine                        │
│ - coverage_tracker: CoverageTracker                      │
│ - crash_detector: CrashDetector                          │
│ - corpus_manager: CorpusManager                          │
│ - queue_scheduler: QueueScheduler                        │
│ - stats: FuzzingStats                                    │
├──────────────────────────────────────────────────────────┤
│ + fuzz(target_cmd, seed_corpus)                          │
│ - _should_stop(): bool                                   │
│ - _handle_crash(crash, input)                            │
│ - _handle_new_coverage(input)                            │
└──────────────────────────────────────────────────────────┘
                    │
                    │ uses
                    ▼
┌──────────────────────────────────────────────────────────┐
│                  MutationEngine                          │
├──────────────────────────────────────────────────────────┤
│ - deterministic: DeterministicMutator                    │
│ - havoc: HavocMutator                                    │
│ - dictionary: DictionaryManager                          │
│ - splice: SpliceMutator                                  │
├──────────────────────────────────────────────────────────┤
│ + mutate(data, strategy): bytes                          │
│ + mutate_batch(data, count): List[bytes]                 │
└──────────────────────────────────────────────────────────┘
                    │
                    │ uses
                    ▼
┌──────────────────────────────────────────────────────────┐
│                 ProtocolParser                           │
├──────────────────────────────────────────────────────────┤
│ <<abstract>>                                             │
├──────────────────────────────────────────────────────────┤
│ + parse(data): ParsedMessage                             │
│ + generate(template): bytes                              │
│ + mutate_field(data, field, mutation): bytes             │
└──────────────────────────────────────────────────────────┘
         △                    △                   △
         │                    │                   │
    ┌────┴────┐          ┌────┴────┐        ┌────┴────┐
    │  HTTP   │          │   DNS   │        │  SMTP   │
    │  Parser │          │  Parser │        │ Parser  │
    └─────────┘          └─────────┘        └─────────┘
```

---

## Execution Flow Timeline

```
Time ──▶

Fuzzing Loop:     [SELECT] [MUTATE] [EXECUTE] [ANALYZE] [REPEAT] ...
                      │        │         │         │
                      ▼        ▼         ▼         ▼
Queue Scheduler:  [PICK]──────┘         │         │
                                        │         │
Mutation Engine:           [APPLY]──────┘         │
                             │                    │
Protocol Parser:             └─[PARSE/GEN]        │
                                                  │
Target Executor:                     [SPAWN]     │
                                       │         │
                                     [FEED INPUT] │
                                       │         │
                                     [MONITOR]   │
                                       │         │
                                     [COLLECT]───┘
                                       │
                           ┌───────────┴───────────┐
                           │                       │
Coverage Tracker:      [RECORD]              [COMPARE]
                           │                       │
                       [BITMAP]            [NEW EDGES?]
                                                  │
Crash Detector:                            [CHECK SIGNALS]
                                                  │
                                           [SANITIZERS?]
                                                  │
                                            [CLASSIFY]
                                                  │
                                         [SAVE/MINIMIZE]
```

---

## Module Dependencies

```
protocrash/
│
├── cli/
│   └── main.py ────────────┐
│                           │
├── fuzzing_engine/         │
│   ├── fuzzer.py ◄─────────┘
│   ├── queue.py ◄──────────────────┐
│   └── corpus.py ◄─────────────┐   │
│                               │   │
├── mutators/                   │   │
│   ├── mutation_engine.py     │   │
│   ├── deterministic.py       │   │
│   ├── havoc.py               │   │
│   ├── dictionary.py          │   │
│   └── splice.py              │   │
│                               │   │
├── parsers/                    │   │
│   ├── protocol_parser.py ◄───┤   │
│   ├── http_parser.py         │   │
│   ├── dns_parser.py          │   │
│   ├── smtp_parser.py         │   │
│   └── binary_parser.py       │   │
│                               │   │
├── monitors/                   │   │
│   ├── coverage.py ◄───────────┤   │
│   ├── crash_detector.py ◄─────┤   │
│   └── sanitizers.py           │   │
│                               │   │
├── reporters/                  │   │
│   ├── crash_reporter.py ◄─────┤   │
│   └── stats.py ◄──────────────┘   │
│                                   │
└── core/                           │
    ├── config.py ◄─────────────────┘
    └── types.py
```

---

## Shared Data Structures

```
┌─────────────────────────────────────────────────────────┐
│                 Shared Memory Region                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────┐       │
│  │      Coverage Bitmap (64KB)                 │       │
│  │  [Edge 0][Edge 1][Edge 2]...[Edge 65535]    │       │
│  └─────────────────────────────────────────────┘       │
│                    ▲                                    │
│                    │                                    │
│              ┌─────┴──────┐                             │
│              │            │                             │
│         Target       Fuzzer                             │
│        Process      Process                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Communication Patterns

### Fuzzer ↔ Target

```
Fuzzer                          Target
  │                               │
  ├── Fork/Exec ─────────────────▶│
  │                               │
  ├── Send Input (stdin) ────────▶│
  │                               │
  │                               ├── Execute
  │                               │
  │                               ├── Write Coverage ──▶ Shared Mem
  │                               │
  │◄── Exit Code ─────────────────┤
  │                               │
  ├── Read Coverage ◄─────────────── Shared Mem
  │                               │
  └── Analyze Results             │
```

### Components Communication

```
FuzzingLoop ──▶ QueueScheduler.next() ──▶ QueueEntry
                                             │
FuzzingLoop ──▶ MutationEngine.mutate() ◄────┘
                      │
                      ▼
FuzzingLoop ──▶ CrashDetector.execute() ──▶ Target Process
                      │                        │
                      ▼                        ▼
                  CrashInfo                 Coverage
                      │                        │
                      ▼                        ▼
FuzzingLoop ◄── SaveCrash              AddCorpus
```

---

Status: Component integration diagrams complete
