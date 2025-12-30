# ProtoCrash - Getting Started Guide

A comprehensive guide to get started with ProtoCrash fuzzing.

---

## Installation

### Requirements
- Python 3.11+
- Linux (recommended) or Windows
- Target application to fuzz

### Install from PyPI
```bash
pip install protocrash
```

### Install from Source
```bash
git clone https://github.com/noobforanonymous/ProtoCrash.git
cd ProtoCrash
pip install -e .
```

### Verify Installation
```bash
protocrash --help
```

---

## Quick Start Tutorial

### Step 1: Prepare Seed Corpus

Create a directory with valid inputs for your target:

```bash
mkdir -p corpus/http_seeds
echo -e "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n" > corpus/http_seeds/get.txt
echo -e "POST /api HTTP/1.1\r\nHost: localhost\r\nContent-Length: 4\r\n\r\ntest" > corpus/http_seeds/post.txt
```

### Step 2: Start Fuzzing

```bash
# Basic fuzzing
protocrash fuzz --target ./your_server --corpus ./corpus --crashes ./crashes

# With protocol specification
protocrash fuzz --target tcp://localhost:8080 --protocol http --corpus ./corpus
```

### Step 3: Monitor Progress

The real-time dashboard shows:
- Executions per second
- Total executions
- Unique crashes found
- Coverage metrics
- Worker status

**Dashboard Controls:**
- `p` - Pause/resume
- `r` - Refresh display
- `q` - Quit gracefully

### Step 4: Analyze Crashes

```bash
# View crash summary
protocrash analyze --crash-dir ./crashes

# Detailed analysis with exploitability
protocrash analyze --crash-dir ./crashes --classify
```

### Step 5: Generate Report

```bash
# HTML report with charts
protocrash report --campaign-dir ./campaign --format html --output report.html
```

---

## Fuzzing Workflow Walkthrough

### Phase 1: Reconnaissance

1. **Identify target:** Binary, network service, or protocol
2. **Gather samples:** Collect valid inputs as seeds
3. **Understand protocol:** Document message formats

### Phase 2: Corpus Preparation

```bash
# Create structured corpus
mkdir -p corpus/{valid,edge_cases,malformed}

# Add valid inputs
cp samples/*.bin corpus/valid/

# Add boundary cases
echo -ne "\x00\x00\x00\x00" > corpus/edge_cases/zeros.bin
echo -ne "\xff\xff\xff\xff" > corpus/edge_cases/max.bin
```

### Phase 3: Fuzzing Campaign

```bash
# Single-process fuzzing
protocrash fuzz \
  --target ./target \
  --corpus ./corpus \
  --crashes ./crashes \
  --timeout 5000

# Distributed fuzzing (faster)
protocrash fuzz \
  --target ./target \
  --corpus ./corpus \
  --crashes ./crashes \
  --workers 8 \
  --duration 3600
```

### Phase 4: Crash Triage

```bash
# Group similar crashes
protocrash analyze --crash-dir ./crashes --dedupe

# Assess exploitability
protocrash analyze --crash-dir ./crashes --classify
```

### Phase 5: Reporting

```bash
# Generate comprehensive report
protocrash report --campaign-dir . --format html --output final_report.html
```

---

## Crash Analysis Guide

### Understanding Crash Types

| Type | Signal | Description | Exploitability |
|------|--------|-------------|----------------|
| SEGV | 11 | Segmentation fault | HIGH |
| ABRT | 6 | Abort (assertion) | MEDIUM |
| FPE | 8 | Floating point exception | LOW |
| BUS | 7 | Bus error | HIGH |
| ILL | 4 | Illegal instruction | HIGH |
| HANG | - | Timeout/infinite loop | LOW |

### Crash Classification

ProtoCrash automatically classifies crashes:

- **CRITICAL:** Control flow hijack potential
- **HIGH:** Memory corruption, arbitrary write
- **MEDIUM:** Denial of service, assertion failures
- **LOW:** Non-exploitable crashes

### Crash Deduplication

Crashes are grouped by:
1. Stack trace hash
2. Crash address
3. Signal type
4. Function name

### Reproducing Crashes

```bash
# Each crash file can reproduce the bug
./target < crashes/crash_001.bin

# Or use analyze command
protocrash analyze --crash-dir ./crashes --type segv
```

---

## Report Generation Guide

### Text Reports

```bash
protocrash report --campaign-dir ./campaign --format text
```

Output includes:
- Campaign summary
- Crash statistics
- Coverage metrics
- Timeline

### JSON Reports

```bash
protocrash report --campaign-dir ./campaign --format json --output report.json
```

Perfect for automation and CI/CD integration.

### HTML Reports

```bash
protocrash report --campaign-dir ./campaign --format html --output report.html
```

Features:
- Interactive Chart.js visualizations
- Performance graphs
- Coverage heatmap
- Crash catalog with details
- Discovery timeline

---

## Advanced Features

### Distributed Fuzzing

```python
from protocrash.distributed import DistributedCoordinator
from protocrash.fuzzing_engine.coordinator import FuzzingConfig

config = FuzzingConfig(
    target_cmd=["./target", "@@"],
    corpus_dir="./corpus",
    crashes_dir="./crashes",
    timeout_ms=5000
)

coordinator = DistributedCoordinator(config, num_workers=8)
coordinator.run(duration=3600)
```

### Custom Protocol Grammars

Define binary protocol structure:

```json
{
  "name": "CustomProtocol",
  "fields": [
    {"name": "magic", "type": "uint32", "value": "0xDEADBEEF"},
    {"name": "length", "type": "uint16"},
    {"name": "command", "type": "uint8"},
    {"name": "payload", "type": "bytes", "length_field": "length"}
  ]
}
```

### Custom Mutation Strategies

```python
from protocrash.mutators.mutation_engine import MutationEngine

engine = MutationEngine()
engine.register_mutator(MyCustomMutator())
```

### Coverage-Guided Feedback

ProtoCrash tracks code coverage to guide mutations toward unexplored paths, maximizing vulnerability discovery.

---

## Troubleshooting

### No crashes found
- Increase timeout: `--timeout 10000`
- Add more diverse seeds
- Use protocol-specific dictionary
- Verify target is actually running

### Slow execution
- Reduce timeout: `--timeout 1000`
- Use faster storage (SSD/RAM disk)
- Enable workers: `--workers 4`
- Minimize corpus size

### False positives
- Verify reproducibility
- Check for timing issues
- Use sanitizers (ASan, MSan)
- Review crash classification

### Memory issues
- Reduce worker count
- Set memory limits
- Monitor with `htop`

---

## Next Steps

1. Read [API Reference](API_REFERENCE.md)
2. Check [Configuration Options](CONFIGURATION.md)
3. Review [Protocol Support](PROTOCOLS.md)
4. Explore [Examples](../examples/)
