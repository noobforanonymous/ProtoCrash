# ProtoCrash - Setup Guide

## System Requirements

### Operating System
- **Linux:** Ubuntu 20.04+, Debian 11+, Arch Linux (recommended)
- **macOS:** macOS 12+ (limited coverage support)
- **Windows:** WSL2 with Ubuntu (not recommended for performance)

### Hardware
- **CPU:** Multi-core processor (4+ cores recommended)
- **RAM:** 4GB minimum, 8GB+ recommended
- **Disk:** 10GB free space for corpus and crashes
- **Network:** Required for fuzzing network protocols

### Software
- **Python:** 3.11 or newer
- **Git:** For cloning repository
- **GDB:** For crash analysis (optional but recommended)
- **Compiler:** GCC/Clang if building coverage-instrumented targets

---

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
# Install latest stable version
pip install protocrash

# Verify installation
protocrash --version
```

### Option 2: Install from Source

```bash
# Clone repository
git clone https://github.com/noobforanonymous/ProtoCrash.git
cd ProtoCrash

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Verify installation
protocrash --version
```

### Option 3: Docker Container

```bash
# Pull Docker image
docker pull noobforanonymous/protocrash:latest

# Run container
docker run -it --rm \
  -v $(pwd)/corpus:/app/corpus \
  -v $(pwd)/crashes:/app/crashes \
  noobforanonymous/protocrash:latest
```

---

## Dependencies

### Core Dependencies

Installed automatically with pip:
- click >= 8.1.0 (CLI framework)
- rich >= 13.0.0 (Terminal formatting)
- pwntools >= 4.11.0 (Process management)
- scapy >= 2.5.0 (Packet manipulation)
- pyshark >= 0.6.0 (Network capture)

### Optional Dependencies

For advanced features:
```bash
# Crash analysis
pip install capstone  # Disassembly

# Network fuzzing
pip install dpkt  # Additional protocol support

# Performance monitoring
pip install psutil

# Coverage visualization
pip install matplotlib
```

---

## Development Setup

### For Contributing

```bash
# Clone with development dependencies
git clone https://github.com/noobforanonymous/ProtoCrash.git
cd ProtoCrash

# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check .
black --check .
```

### Development Tools

Tools used in development:
- **pytest:** Testing framework
- **ruff:** Fast Python linter
- **black:** Code formatter
- **mypy:** Type checking (optional)
- **pre-commit:** Git hooks for code quality

---

## Configuration

### Environment Variables

```bash
# Set corpus directory (default: ./corpus)
export PROTOCRASH_CORPUS=/path/to/corpus

# Set crash output directory (default: ./crashes)
export PROTOCRASH_CRASHES=/path/to/crashes

# Set log level (DEBUG, INFO, WARNING, ERROR)
export PROTOCRASH_LOG_LEVEL=INFO

# Enable coverage tracking
export PROTOCRASH_COVERAGE=1
```

### Configuration File

Create `~/.protocrash/config.json`:

```json
{
  "corpus_dir": "./corpus",
  "crashes_dir": "./crashes",
  "timeout": 5000,
  "memory_limit": "512M",
  "cpu_limit": 1,
  "parallel_workers": 4,
  "log_level": "INFO",
  "coverage_enabled": true
}
```

---

## Verifying Installation

### Quick Test

```bash
# Run self-test
protocrash test

# Expected output:
# [OK] Python version: 3.11.x
# [OK] Dependencies installed
# [OK] Coverage tracking available
# [OK] Process management working
# All tests passed!
```

### Test Fuzzing

```bash
# Create test corpus
mkdir -p corpus
echo "GET / HTTP/1.1\r\nHost: test\r\n\r\n" > corpus/http-get.txt

# Fuzz localhost HTTP server
python3 -m http.server 8080 &
protocrash fuzz --target http://localhost:8080 --protocol http --timeout 5

# Should start fuzzing and show stats
```

---

## Target Preparation

### Coverage-Instrumented Binaries

For maximum effectiveness, compile targets with coverage instrumentation:

**GCC:**
```bash
gcc -fprofile-arcs -ftest-coverage target.c -o target
```

**Clang:**
```bash
clang -fsanitize=address,fuzzer-no-link target.c -o target
```

**CMake:**
```cmake
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fprofile-arcs -ftest-coverage")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-arcs -ftest-coverage")
```

### Building Test Targets

Example vulnerable server for testing:

```c
// test_server.c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main() {
    char buffer[64];
    printf("Enter input: ");
    gets(buffer);  // Intentionally vulnerable
    printf("You entered: %s\n", buffer);
    return 0;
}
```

Build:
```bash
gcc -fno-stack-protector -z execstack test_server.c -o test_server
```

---

## Troubleshooting

### Common Issues

**1. Permission denied when fuzzing**
```bash
# Solution: Run with appropriate permissions
sudo protocrash fuzz ...
# Or adjust target permissions
```

**2. Coverage not working**
```bash
# Check if coverage module is available
python3 -c "import coverage; print(coverage.__version__)"

# Rebuild target with coverage flags
```

**3. Too many open files**
```bash
# Increase file descriptor limit
ulimit -n 8192
```

**4. Process timeout issues**
```bash
# Increase timeout value
protocrash fuzz --timeout 10000  # 10 seconds
```

### Getting Help

- GitHub Issues: https://github.com/noobforanonymous/ProtoCrash/issues
- Documentation: https://protocrash.readthedocs.io
- Discord: [Community Server Link]

---

## System Optimization

### For Maximum Performance

```bash
# Disable ASLR (testing only!)
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space

# Increase core dump size limit
ulimit -c unlimited

# Set CPU governor to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Disable swap
sudo swapoff -a
```

### Resource Limits

Edit `/etc/security/limits.conf`:
```
* soft nofile 8192
* hard nofile 16384
* soft core unlimited
* hard core unlimited
```

---

## Next Steps

After setup is complete:

1. Read [Usage Guide](../USAGE.md) for fuzzing examples
2. Study [System Architecture](../architecture/SYSTEM_ARCHITECTURE.md)
3. Review [Ethical Guidelines](../guidelines/ETHICAL_GUIDELINES.md)
4. Start fuzzing your first target

---

Status: Setup complete, ready to fuzz!
