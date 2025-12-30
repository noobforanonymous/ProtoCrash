# ProtoCrash - Example Workflows

This directory contains example workflows for common fuzzing scenarios.

---

## 1. Basic Fuzzing Campaign

### Setup
```bash
cd examples
mkdir -p campaign/{corpus,crashes}
```

### Create Seeds
```bash
# HTTP seeds
echo -e "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n" > campaign/corpus/get.txt
echo -e "POST /api HTTP/1.1\r\nContent-Length: 4\r\n\r\ntest" > campaign/corpus/post.txt
```

### Run Fuzzing
```bash
protocrash fuzz \
  --target ./targets/http_server.py \
  --corpus ./campaign/corpus \
  --crashes ./campaign/crashes \
  --timeout 5000 \
  --duration 300
```

### Analyze Results
```bash
protocrash analyze --crash-dir ./campaign/crashes --classify
protocrash report --campaign-dir ./campaign --format html --output report.html
```

---

## 2. Distributed Fuzzing Setup

### Configuration
```python
# distributed_fuzz.py
from protocrash.distributed import DistributedCoordinator
from protocrash.fuzzing_engine.coordinator import FuzzingConfig

config = FuzzingConfig(
    target_cmd=["python3", "targets/http_server.py", "@@"],
    corpus_dir="./campaign/corpus",
    crashes_dir="./campaign/crashes",
    timeout_ms=5000
)

coordinator = DistributedCoordinator(
    config,
    num_workers=8,
    sync_interval=5.0
)

# Add seeds
coordinator.add_seed(b"GET / HTTP/1.1\r\n\r\n")
coordinator.add_seed(b"POST /api HTTP/1.1\r\n\r\ntest")

# Run for 1 hour
coordinator.run(duration=3600)
```

### Execute
```bash
python3 distributed_fuzz.py
```

---

## 3. Crash Triage Workflow

### Step 1: Collect Crashes
```bash
# After fuzzing, crashes are in ./campaign/crashes
ls -la ./campaign/crashes/
```

### Step 2: Deduplicate
```bash
protocrash analyze --crash-dir ./campaign/crashes --dedupe
```

### Step 3: Classify
```bash
protocrash analyze --crash-dir ./campaign/crashes --classify
```

### Step 4: Filter by Type
```bash
# View only segfaults
protocrash analyze --crash-dir ./campaign/crashes --type segv
```

### Step 5: Reproduce
```bash
# Reproduce specific crash
./targets/http_server.py < ./campaign/crashes/crash_001.bin
```

---

## 4. Report Generation

### Text Report
```bash
protocrash report --campaign-dir ./campaign --format text
```

### JSON Report (for CI/CD)
```bash
protocrash report --campaign-dir ./campaign --format json --output report.json
```

### HTML Report (with charts)
```bash
protocrash report --campaign-dir ./campaign --format html --output report.html
xdg-open report.html
```

---

## 5. Protocol-Specific Workflows

### HTTP Fuzzing
```bash
protocrash fuzz \
  --target tcp://localhost:8080 \
  --protocol http \
  --corpus ./http_corpus \
  --dictionary ./dictionaries/http_keywords.txt
```

### DNS Fuzzing
```bash
protocrash fuzz \
  --target udp://localhost:5353 \
  --protocol dns \
  --corpus ./dns_corpus
```

### Binary Protocol
```bash
protocrash fuzz \
  --target ./targets/custom_protocol.py \
  --protocol binary \
  --grammar ./configs/custom_protocol.json
```

---

## 6. CI/CD Integration

### GitHub Actions
```yaml
# .github/workflows/fuzz.yml
name: Fuzzing
on: [push]
jobs:
  fuzz:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install protocrash
      - run: |
          protocrash fuzz \
            --target ./app \
            --corpus ./seeds \
            --crashes ./crashes \
            --max-time 300
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: crashes
          path: crashes/
```
