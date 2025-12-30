# ProtoCrash - Usage Guide

## Quick Start

### Basic Fuzzing

```bash
# Fuzz HTTP server
protocrash fuzz --target http://localhost:8080 --protocol http

# Fuzz custom binary protocol over TCP
protocrash fuzz --target tcp://192.168.1.100:9000 --protocol binary --grammar protocol.json

# Fuzz with seed corpus
protocrash fuzz --target ./binary --corpus ./seeds --timeout 5000
```

---

## Command Reference

### Main Commands

#### `protocrash fuzz`
Start fuzzing a target

```bash
protocrash fuzz [OPTIONS] --target TARGET

Options:
  --target TEXT          Target to fuzz (URL, IP:PORT, or binary path) [required]
  --protocol TEXT        Protocol type (http, dns, smtp, binary, custom)
  --corpus PATH          Directory containing seed inputs
  --timeout INTEGER      Execution timeout in milliseconds [default: 5000]
  --memory-limit TEXT    Memory limit (e.g., 512M, 1G) [default: 1G]
  --workers INTEGER      Number of parallel workers [default: 1]
  --max-time INTEGER     Stop after N seconds
  --max-execs INTEGER    Stop after N executions
  --dictionary PATH      Dictionary file for mutations
  --output PATH          Output directory for crashes [default: ./crashes]
  --coverage             Enable coverage tracking
  --verbose              Enable verbose logging
```

Examples:
```bash
# Basic HTTP fuzzing
protocrash fuzz --target http://localhost:8080 --protocol http

# Multi-core fuzzing with custom corpus
protocrash fuzz --target ./server --corpus ./seeds --workers 4

# Fuzzing with time limit
protocrash fuzz --target tcp://target:9000 --max-time 3600  # 1 hour
```

---

#### `protocrash analyze`
Analyze crashes

```bash
protocrash analyze [OPTIONS] CRASH_DIR

Options:
  --triage              Group similar crashes
  --minimize            Minimize crash inputs
  --exploitability      Analyze crash exploitability
  --report PATH         Generate HTML report
  --stack-depth INT     Stack trace depth [default: 10]
```

Examples:
```bash
# Basic crash analysis
protocrash analyze ./crashes

# Generate HTML report
protocrash analyze ./crashes --report crash_report.html

# Minimize and triage
protocrash analyze ./crashes --minimize --triage
```

---

#### `protocrash corpus`
Manage corpus

```bash
protocrash corpus [COMMAND] [OPTIONS]

Commands:
  minimize    Minimize corpus size
  merge       Merge multiple corpora
  stats       Show corpus statistics
  validate    Validate corpus inputs
```

Examples:
```bash
# Show corpus stats
protocrash corpus stats ./corpus

# Minimize corpus (remove redundant inputs)
protocrash corpus minimize ./corpus --output ./corpus_min

# Merge two corpora
protocrash corpus merge corpus1 corpus2 --output merged_corpus
```

---

#### `protocrash monitor`
Monitor fuzzing progress

```bash
protocrash monitor [OPTIONS] SESSION_ID

Options:
  --live              Live updating display
  --refresh INT       Refresh interval in seconds [default: 1]
  --export PATH       Export stats to file
```

Examples:
```bash
# Monitor fuzzing session
protocrash monitor fuzzing_session_001

# Export statistics
protocrash monitor fuzzing_session_001 --export stats.json
```

---

## Protocol-Specific Usage

### HTTP Fuzzing

```bash
# Basic HTTP GET fuzzing
protocrash fuzz \
  --target http://localhost:8080 \
  --protocol http \
  --corpus ./http_seeds

# HTTP POST fuzzing with custom headers
cat > http_template.json << EOF
{
  "method": "POST",
  "path": "/api/upload",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer TOKEN"
  },
  "body_template": "FUZZ_HERE"
}
EOF

protocrash fuzz \
  --target http://localhost:8080 \
  --protocol http \
  --template http_template.json
```

### DNS Fuzzing

```bash
# Fuzz DNS server
protocrash fuzz \
  --target udp://8.8.8.8:53 \
  --protocol dns \
  --dictionary dns_keywords.txt

# Create DNS seed corpus
mkdir -p dns_seeds
echo -ne "\x00\x00\x01\x00\x00\x01" > dns_seeds/query.bin

protocrash fuzz \
  --target udp://localhost:5353 \
  --protocol dns \
  --corpus ./dns_seeds
```

### Custom Binary Protocol

Define protocol grammar (protocol.json):
```json
{
  "name": "CustomProtocol",
  "fields": [
    {
      "name": "magic",
      "type": "uint32",
      "value": "0xDEADBEEF"
    },
    {
      "name": "length",
      "type": "uint16",
      "computed": "len(payload)"
    },
    {
      "name": "command",
      "type": "uint8",
      "values": [1, 2, 3, 4]
    },
    {
      "name": "payload",
      "type": "bytes",
      "max_length": 1024
    }
  ]
}
```

Fuzz:
```bash
protocrash fuzz \
  --target tcp://localhost:9000 \
  --protocol binary \
  --grammar protocol.json \
  --corpus ./seeds
```

---

## Advanced Usage

### Dictionary-Based Fuzzing

Create dictionary (keywords.txt):
```
GET
POST
HTTP/1.1
Content-Length
Authorization
admin
root
../../../etc/passwd
%s%s%s%s
\x00\x00\x00\x00
```

Use:
```bash
protocrash fuzz \
  --target http://localhost:8080 \
  --dictionary keywords.txt
```

### Mutation Strategies

Configure mutations (mutations.yaml):
```yaml
mutations:
  - type: bitflip
    weight: 30
  - type: byteflip
    weight: 20
  - type: arithmetic
    weight: 15
  - type: interesting_values
    weight: 10
  - type: dictionary
    weight: 15
  - type: havoc
    weight: 10
```

Use:
```bash
protocrash fuzz \
  --target ./binary \
  --mutations mutations.yaml
```

### Coverage-Guided Fuzzing

```bash
# Compile target with coverage
gcc -fprofile-arcs -ftest-coverage target.c -o target

# Fuzz with coverage tracking
protocrash fuzz \
  --target ./target \
  --coverage \
  --corpus ./seeds \
  --workers 4
```

### Distributed Fuzzing

```bash
# Start coordinator
protocrash coordinator start --port 6666

# Start worker 1
protocrash fuzz \
  --target ./binary \
  --distributed \
  --coordinator localhost:6666 \
  --worker-id 1

# Start worker 2 on different machine
protocrash fuzz \
  --target ./binary \
  --distributed \
  --coordinator 192.168.1.100:6666 \
  --worker-id 2
```

---

## Crash Triage Workflow

### 1. Initial Analysis

```bash
# Analyze crashes
protocrash analyze ./crashes --triage
```

Output:
```
Crash Summary:
  Total crashes: 127
  Unique crashes: 5
  
Buckets:
  [SIGSEGV] null_deref: 89 crashes
  [SIGSEGV] heap_overflow: 23 crashes
  [SIGABRT] assert_fail: 12 crashes
  [SIGSEGV] stack_overflow: 2 crashes
  [SIGILL] bad_instruction: 1 crash
```

### 2. Minimize Crashes

```bash
# Minimize each crash bucket
for crash in crashes/unique/*.crash; do
  protocrash analyze $crash --minimize
done
```

### 3. Generate Reports

```bash
# Create detailed HTML report
protocrash analyze ./crashes \
  --triage \
  --minimize \
  --exploitability \
  --report full_report.html
```

### 4. Reproduce Crashes

```bash
# Reproduce specific crash
protocrash reproduce ./crashes/unique/crash_001.crash --target ./binary
```

---

## Best Practices

### Corpus Management

1. **Start with valid inputs:** Seed corpus with valid protocol messages
2. **Keep corpus small:** Minimize regularly to avoid redundancy
3. **Diverse inputs:** Include edge cases and boundary values
4. **Regular updates:** Add interesting findings to corpus

### Performance Optimization

1. **Use `--workers`:** Leverage multi-core systems
2. **Tune timeout:** Balance between speed and coverage
3. **Monitor resources:** Watch CPU, memory, disk usage
4. **Batch processing:** Process large targets in chunks

### Crash Analysis

1. **Triage first:** Group similar crashes before deep analysis
2. **Minimize inputs:** Smaller reproducers are easier to analyze
3. **Check exploitability:** Prioritize exploitable crashes
4. **Document findings:** Keep detailed notes

---

## Integration

### CI/CD Integration

```bash
# GitLab CI example
fuzz_test:
  script:
    - pip install protocrash
    - protocrash fuzz --target ./app --max-time 300 --max-execs 10000
    - if [ -d crashes ]; then exit 1; fi
  artifacts:
    paths:
      - crashes/
    when: on_failure
```

### Automated Testing

```python
# Python automation
import subprocess
import os

def run_fuzzer(target, duration):
    cmd = [
        "protocrash", "fuzz",
        "--target", target,
        "--max-time", str(duration),
        "--corpus", "./seeds"
    ]
    result = subprocess.run(cmd, capture_output=True)
    
    # Check for crashes
    if os.path.exists("./crashes"):
        return list(Path("./crashes").glob("*.crash"))
    return []

crashes = run_fuzzer("./myapp", 3600)
if crashes:
    print(f"Found {len(crashes)} crashes!")
```

---

## Troubleshooting

### No crashes found

1. Increase timeout: `--timeout 10000`
2. Add more seed inputs to corpus
3. Use dictionary for better mutations
4. Check if target is actually vulnerable

### Too slow

1. Reduce timeout: `--timeout 1000`
2. Use faster mutation strategies
3. Enable multi-core: `--workers 4`
4. Minimize corpus

### False positives

1. Verify crashes are reproducible
2. Check for timing issues
3. Review crash analysis output
4. Test with sanitizers (ASan, MSan)

---

## Examples

See `examples/` directory for:
- HTTP server fuzzing
- DNS protocol fuzzing
- Custom protocol examples
- Crash analysis scripts
- Integration examples

---

Status: Ready to start fuzzing!
