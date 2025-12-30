# ProtoCrash Examples

This directory contains examples for using ProtoCrash.

## Directory Structure

```
examples/
├── targets/              # Example fuzzing targets
│   ├── http_server.py    # Vulnerable HTTP server
│   ├── dns_server.py     # Vulnerable DNS server
│   └── custom_protocol.py # Vulnerable binary protocol
├── workflows/            # Workflow documentation
│   └── README.md         # Common fuzzing workflows
├── configs/              # Configuration examples
│   └── protocrash.yaml   # Sample config file
├── scripts/              # Utility scripts
│   ├── run_demo.sh       # End-to-end demo
│   └── generate_corpus.py # Corpus generator
├── corpus/               # (Generated) Seed inputs
└── BEST_PRACTICES.md     # Fuzzing guidelines
```

## Quick Start

### 1. Generate Corpus
```bash
python3 scripts/generate_corpus.py --output ./corpus --protocol all
```

### 2. Run Demo
```bash
chmod +x scripts/run_demo.sh
./scripts/run_demo.sh
```

### 3. Manual Fuzzing
```bash
# HTTP target
protocrash fuzz \
  --target ./targets/http_server.py \
  --corpus ./corpus/http \
  --crashes ./crashes

# DNS target
protocrash fuzz \
  --target ./targets/dns_server.py \
  --corpus ./corpus/dns \
  --crashes ./crashes

# Custom protocol
protocrash fuzz \
  --target ./targets/custom_protocol.py \
  --corpus ./corpus/binary \
  --crashes ./crashes
```

## Security Warning

**These targets contain intentional vulnerabilities for demonstration purposes.**

- DO NOT use in production
- DO NOT expose to networks
- For testing only

## Learn More

- [Workflow Examples](workflows/README.md)
- [Best Practices](BEST_PRACTICES.md)
- [Configuration Guide](../docs/CONFIGURATION.md)
- [API Reference](../docs/API_REFERENCE.md)
