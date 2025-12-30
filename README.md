# ProtoCrash

**Coverage-Guided Protocol Fuzzer for Vulnerability Discovery**

ProtoCrash is a smart mutation-based fuzzer designed to find crashes and vulnerabilities in network protocol implementations. Built with intelligent feedback-driven fuzzing techniques, it targets custom protocols, binary formats, and network services.

## Features

- **Coverage-Guided Fuzzing** - AFL-style instrumentation for intelligent test case generation
- **Distributed Fuzzing** - Multi-process parallelization for maximum throughput
- **Multi-Protocol Support** - HTTP, DNS, SMTP, custom binary protocols
- **Smart Mutation Engine** - Context-aware mutations based on protocol structure
- **Crash Detection** - Automatic crash analysis, classification, and exploitability assessment
- **Real-Time Dashboard** - Live fuzzing statistics with keyboard controls
- **Report Generation** - Text, JSON, and HTML reports with visualizations
- **Minimal Dependencies** - Pure Python implementation
- **Extensible** - Easy to add custom protocol parsers and mutation strategies

## Installation

```bash
pip install protocrash
```

Or install from source:

```bash
git clone https://github.com/noobforanonymous/ProtoCrash.git
cd ProtoCrash
pip install -e .
```

## CLI Usage

### Fuzzing Commands

```bash
# Basic fuzzing with real-time dashboard
protocrash fuzz --target ./vulnerable_app --corpus ./seeds --crashes ./crashes

# Distributed fuzzing with 8 workers
protocrash fuzz --target ./vulnerable_app --workers 8 --duration 3600

# Protocol-specific fuzzing
protocrash fuzz --target tcp://localhost:8080 --protocol http --timeout 5000
```

### Crash Analysis

```bash
# Analyze crashes with exploitability assessment
protocrash analyze --crash-dir ./crashes

# Classify and deduplicate crashes
protocrash analyze --crash-dir ./crashes --dedupe --classify

# Filter by crash type
protocrash analyze --crash-dir ./crashes --type segv
```

### Report Generation

```bash
# Generate text report
protocrash report --campaign-dir ./campaign --format text

# Generate HTML report with charts
protocrash report --campaign-dir ./campaign --format html --output report.html

# Generate JSON report for automation
protocrash report --campaign-dir ./campaign --format json --output report.json
```

### Dashboard Controls

When running the real-time dashboard:
- `p` - Pause/resume fuzzing
- `r` - Refresh display
- `q` - Quit gracefully

## Distributed Fuzzing

ProtoCrash supports multi-process distributed fuzzing for increased throughput.

### Python API

```python
from protocrash.distributed import DistributedCoordinator
from protocrash.fuzzing_engine.coordinator import FuzzingConfig

config = FuzzingConfig(
    target_cmd=["./target", "@@"],
    corpus_dir="./corpus",
    crashes_dir="./crashes",
    timeout_ms=5000
)

# Launch distributed fuzzing with 8 workers
coordinator = DistributedCoordinator(config, num_workers=8)
coordinator.run(duration=3600)  # Run for 1 hour
```

### Architecture

- **Master-Worker Model**: One coordinator process manages N worker processes
- **Corpus Synchronization**: Workers share interesting test cases via filesystem
- **Statistics Aggregation**: Real-time performance metrics from all workers
- **Crash Deduplication**: Unique crash detection across all workers

### Performance

Distributed fuzzing scales efficiently:
- 1 worker: ~50,000 exec/sec
- 4 workers: ~180,000 exec/sec  
- 8 workers: ~350,000 exec/sec
- Scaling efficiency: ~87.5%

## Project Status

| Metric | Value |
|--------|-------|
| Tests | 859 passing (100%) |
| Coverage | 96% |
| Production Code | 9,093 lines |
| Test Code | 12,661 lines |
| Platforms | Linux (full), Windows (partial) |

## Documentation

- [Usage Guide](docs/USAGE.md)
- [Setup Instructions](docs/implementation/SETUP.md)
- [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)
- [Fuzzing Engine Details](docs/implementation/FUZZER_ENGINE.md)
- [Distributed Fuzzing Guide](progress/day24-25_progress.md)
- [CLI & Reporting](progress/day26-27_progress.md)

## How It Works

```
Input Corpus → Smart Mutation → Target Execution → Coverage Feedback → Crash Detection
      ↑                                                      ↓
      └──────────────── New Interesting Cases ──────────────┘
```

ProtoCrash uses coverage-guided fuzzing to intelligently generate test cases that explore new code paths in the target application. It monitors the target for crashes, hangs, and memory corruption, automatically saving reproducible test cases.

## Requirements

- Python 3.11+
- Linux (recommended for best coverage support)
- Target application for fuzzing

## Ethical Use

ProtoCrash is designed exclusively for authorized security testing, vulnerability research, and software quality assurance. Only use this tool on systems you own or have explicit permission to test.

See [Ethical Guidelines](docs/guidelines/ETHICAL_GUIDELINES.md) for detailed usage policy.

## Author

**Regaan**
- GitHub: [@noobforanonymous](https://github.com/noobforanonymous)

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

Built with inspiration from AFL, LibFuzzer, and Boofuzz. Designed for the security research community.
