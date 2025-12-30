# ProtoCrash - Configuration Options

Complete configuration reference for ProtoCrash.

---

## Command Line Options

### Fuzzing Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--target` | TEXT | required | Target binary or URL |
| `--corpus` | PATH | ./corpus | Seed corpus directory |
| `--crashes` | PATH | ./crashes | Crash output directory |
| `--protocol` | TEXT | auto | Protocol type (http, dns, smtp, binary) |
| `--timeout` | INT | 5000 | Execution timeout (ms) |
| `--workers` | INT | 1 | Parallel worker count |
| `--duration` | INT | None | Campaign duration (seconds) |
| `--max-execs` | INT | None | Maximum executions |
| `--memory-limit` | TEXT | 1G | Memory limit per process |
| `--dictionary` | PATH | None | Dictionary file for mutations |

### Analysis Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--crash-dir` | PATH | required | Directory with crashes |
| `--classify` | FLAG | False | Classify by exploitability |
| `--dedupe` | FLAG | False | Deduplicate crashes |
| `--type` | TEXT | None | Filter by crash type |
| `--minimize` | FLAG | False | Minimize crash inputs |

### Report Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--campaign-dir` | PATH | required | Campaign directory |
| `--format` | TEXT | text | Output format (text, json, html) |
| `--output` | PATH | stdout | Output file path |

---

## Environment Variables

```bash
# Core settings
export PROTOCRASH_TIMEOUT=5000       # Default timeout (ms)
export PROTOCRASH_WORKERS=4          # Default worker count
export PROTOCRASH_MEMORY_LIMIT=1G    # Default memory limit

# Features
export PROTOCRASH_COVERAGE=1         # Enable coverage tracking
export PROTOCRASH_DEBUG=1            # Enable debug logging
export PROTOCRASH_NO_COLOR=1         # Disable colored output

# Paths
export PROTOCRASH_CORPUS_DIR=./corpus
export PROTOCRASH_CRASHES_DIR=./crashes
export PROTOCRASH_CONFIG_FILE=./protocrash.yaml
```

---

## Configuration File

Create `protocrash.yaml` in project root:

```yaml
# Fuzzing settings
fuzzer:
  timeout_ms: 5000
  memory_limit: "1G"
  workers: 4
  max_iterations: null

# Corpus management
corpus:
  sync_interval: 5.0
  minimize: true
  dedup: true

# Mutation settings
mutations:
  strategies:
    - bitflip: 30
    - byteflip: 20
    - arithmetic: 15
    - interesting: 10
    - dictionary: 15
    - havoc: 10

# Reporting
reporting:
  format: html
  charts: true
  include_inputs: false

# Distributed fuzzing
distributed:
  sync_interval: 5.0
  stats_interval: 2.0
```

---

## Protocol Configuration

### HTTP Protocol

```yaml
protocol:
  type: http
  settings:
    methods: [GET, POST, PUT, DELETE]
    headers:
      - Content-Type
      - Authorization
    paths: [/, /api, /admin]
```

### DNS Protocol

```yaml
protocol:
  type: dns
  settings:
    query_types: [A, AAAA, MX, TXT, NS]
    domains: [example.com, test.local]
```

### Binary Protocol

```yaml
protocol:
  type: binary
  grammar: protocol.json
  endianness: little
```

---

## Performance Tuning

### For Speed

```yaml
fuzzer:
  timeout_ms: 1000    # Lower timeout
  workers: 8          # More workers
  
corpus:
  minimize: true      # Smaller corpus
```

### For Coverage

```yaml
fuzzer:
  timeout_ms: 10000   # Higher timeout
  workers: 2          # Fewer workers
  
mutations:
  strategies:
    - havoc: 40       # More aggressive
```

### For Stability

```yaml
fuzzer:
  timeout_ms: 5000
  memory_limit: "512M"
  workers: 2

corpus:
  sync_interval: 10.0
```
