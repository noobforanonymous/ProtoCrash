# ProtoCrash - API Reference

Complete API documentation for ProtoCrash modules.

---

## Core Types

### CrashInfo

```python
from protocrash.core.types import CrashInfo, CrashType

crash = CrashInfo(
    crashed=True,
    crash_type=CrashType.SEGV,
    signal_number=11,
    exit_code=0,
    stdout=b"",
    stderr=b"Segmentation fault",
    stack_trace="#0 0x401234 in main()",
    input_data=b"crash_input"
)
```

**Attributes:**
- `crashed: bool` - Whether crash occurred
- `crash_type: CrashType` - Type of crash (SEGV, ABRT, etc.)
- `signal_number: int` - Unix signal number
- `exit_code: int` - Process exit code
- `stdout: bytes` - Captured stdout
- `stderr: bytes` - Captured stderr
- `stack_trace: str` - Parsed stack trace
- `input_data: bytes` - Input that caused crash

### CrashType

```python
from protocrash.core.types import CrashType

CrashType.SEGV   # Segmentation fault
CrashType.ABRT   # Abort
CrashType.BUS    # Bus error
CrashType.FPE    # Floating point exception
CrashType.ILL    # Illegal instruction
CrashType.HANG   # Timeout/hang
CrashType.ASAN   # AddressSanitizer
```

---

## Fuzzing Engine

### FuzzingConfig

```python
from protocrash.fuzzing_engine.coordinator import FuzzingConfig

config = FuzzingConfig(
    target_cmd=["./target", "@@"],  # @@ = input file
    corpus_dir="./corpus",
    crashes_dir="./crashes",
    timeout_ms=5000,
    memory_limit="1G",
    max_iterations=None  # None = infinite
)
```

**Parameters:**
- `target_cmd: List[str]` - Command to execute target
- `corpus_dir: str` - Path to corpus directory
- `crashes_dir: str` - Path to save crashes
- `timeout_ms: int` - Execution timeout in milliseconds
- `memory_limit: str` - Memory limit (e.g., "512M", "1G")
- `max_iterations: int` - Maximum fuzzing iterations

### FuzzingCoordinator

```python
from protocrash.fuzzing_engine.coordinator import FuzzingCoordinator

coordinator = FuzzingCoordinator(config)
coordinator.add_seed(b"initial_input")
coordinator.run(max_iterations=10000)
```

**Methods:**
- `add_seed(data: bytes)` - Add seed to corpus
- `run(max_iterations: int)` - Start fuzzing
- `stop()` - Stop fuzzing gracefully
- `get_stats()` - Get current statistics

### FuzzingStats

```python
from protocrash.fuzzing_engine.stats import FuzzingStats

stats = coordinator.stats
print(f"Executions: {stats.total_execs}")
print(f"Crashes: {stats.unique_crashes}")
print(f"Exec/sec: {stats.execs_per_sec}")
```

**Attributes:**
- `total_execs: int` - Total executions
- `unique_crashes: int` - Unique crashes found
- `unique_hangs: int` - Unique hangs found
- `execs_per_sec: float` - Execution rate
- `start_time: float` - Campaign start time

---

## Distributed Fuzzing

### DistributedCoordinator

```python
from protocrash.distributed import DistributedCoordinator

coordinator = DistributedCoordinator(
    config,
    num_workers=8,        # Number of parallel workers
    sync_interval=5.0     # Corpus sync interval (seconds)
)

coordinator.add_seed(b"seed")
coordinator.run(duration=3600)  # Run for 1 hour
```

**Parameters:**
- `config: FuzzingConfig` - Fuzzing configuration
- `num_workers: int` - Worker count (default: CPU count)
- `sync_interval: float` - Corpus sync interval

**Methods:**
- `run(duration: float)` - Run campaign for duration
- `add_seed(data: bytes)` - Add initial seed

### StatsAggregator

```python
from protocrash.distributed.stats_aggregator import StatsAggregator

aggregator = StatsAggregator(num_workers=8)
stats = aggregator.get_aggregate_stats()
```

**Methods:**
- `update_worker_stats(worker_id, stats)` - Update worker stats
- `get_aggregate_stats()` - Get combined statistics
- `display_stats()` - Print stats to console

---

## Mutators

### MutationEngine

```python
from protocrash.mutators.mutation_engine import MutationEngine

engine = MutationEngine()
mutated = engine.mutate(b"original_input")
```

**Methods:**
- `mutate(data: bytes) -> bytes` - Apply random mutation
- `register_mutator(mutator)` - Add custom mutator

### Protocol Mutators

```python
from protocrash.mutators.http_mutator import HTTPMutator
from protocrash.mutators.dns_mutator import DNSMutator
from protocrash.mutators.smtp_mutator import SMTPMutator

http_mutator = HTTPMutator()
mutated = http_mutator.mutate(b"GET / HTTP/1.1\r\n\r\n")
```

### BinaryMutator

```python
from protocrash.mutators.binary_mutator import BinaryMutator
from protocrash.protocols.binary_grammar import Grammar, UInt8, Bytes

grammar = Grammar("Protocol", [
    UInt8("type"),
    Bytes("data", length_field="length")
])

mutator = BinaryMutator(grammar)
mutated = mutator.mutate(b"\x01\x05Hello")
```

---

## Monitors

### CrashClassifier

```python
from protocrash.monitors.crash_classifier import CrashClassifier

result = CrashClassifier.assess_exploitability(crash_info)
# Returns: "NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"
```

### CoverageMap

```python
from protocrash.monitors.coverage_map import CoverageMap

coverage = CoverageMap(map_size=65536)
coverage.update(edge_hash)
print(f"Edges: {coverage.count_edges()}")
```

---

## Parsers

### Protocol Parsers

```python
from protocrash.parsers.http_parser import HTTPParser
from protocrash.parsers.dns_parser import DNSParser
from protocrash.parsers.binary_parser import BinaryParser

parser = HTTPParser()
request = parser.parse(b"GET / HTTP/1.1\r\n\r\n")
```

---

## CLI Commands

### protocrash fuzz

```bash
protocrash fuzz [OPTIONS]

Options:
  --target TEXT      Target binary or URL [required]
  --corpus PATH      Corpus directory
  --crashes PATH     Crashes output directory
  --protocol TEXT    Protocol type (http, dns, smtp, binary)
  --timeout INT      Execution timeout (ms) [default: 5000]
  --workers INT      Parallel workers [default: 1]
  --duration INT     Campaign duration (seconds)
  --help             Show help
```

### protocrash analyze

```bash
protocrash analyze [OPTIONS]

Options:
  --crash-dir PATH   Directory with crashes [required]
  --classify         Classify by exploitability
  --dedupe           Deduplicate crashes
  --type TEXT        Filter by crash type
  --help             Show help
```

### protocrash report

```bash
protocrash report [OPTIONS]

Options:
  --campaign-dir PATH  Campaign directory [required]
  --format TEXT        Output format: text, json, html
  --output PATH        Output file path
  --help               Show help
```

---

## Configuration Options

### Environment Variables

```bash
PROTOCRASH_TIMEOUT=5000      # Default timeout (ms)
PROTOCRASH_WORKERS=4         # Default worker count
PROTOCRASH_COVERAGE=1        # Enable coverage
PROTOCRASH_DEBUG=1           # Debug logging
```

### Config File

```yaml
# protocrash.yaml
fuzzer:
  timeout_ms: 5000
  memory_limit: "1G"
  workers: 4

corpus:
  sync_interval: 5.0
  minimize: true

reporting:
  format: html
  charts: true
```

---

## Error Handling

```python
from protocrash.core.types import CrashInfo

try:
    coordinator.run(max_iterations=1000)
except KeyboardInterrupt:
    coordinator.stop()
    stats = coordinator.get_stats()
    print(f"Stopped after {stats.total_execs} executions")
```

---

## Examples

See the `examples/` directory for complete usage examples.
