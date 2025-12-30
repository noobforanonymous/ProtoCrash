# ProtoCrash - Troubleshooting Guide

Common issues and solutions for ProtoCrash.

---

## Installation Issues

### Python version error

**Error:** `Python 3.11+ required`

**Solution:**
```bash
# Check Python version
python3 --version

# Install Python 3.11+
# Ubuntu/Debian
sudo apt install python3.11

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install protocrash
```

### Missing dependencies

**Error:** `ModuleNotFoundError: No module named 'click'`

**Solution:**
```bash
pip install click rich jinja2
# Or reinstall protocrash
pip install --force-reinstall protocrash
```

---

## Fuzzing Issues

### No crashes found

**Causes:**
1. Target is not vulnerable
2. Timeout too short
3. Poor seed corpus
4. Wrong protocol

**Solutions:**
```bash
# Increase timeout
protocrash fuzz --target ./app --timeout 10000

# Use more diverse seeds
mkdir corpus
echo -e "valid input 1" > corpus/seed1.txt
echo -e "valid input 2" > corpus/seed2.txt
protocrash fuzz --target ./app --corpus ./corpus

# Add dictionary
protocrash fuzz --target ./app --dictionary keywords.txt
```

### Slow execution

**Causes:**
1. High timeout value
2. Single worker mode
3. Large corpus
4. Disk I/O bottleneck

**Solutions:**
```bash
# Lower timeout
protocrash fuzz --target ./app --timeout 1000

# Add workers
protocrash fuzz --target ./app --workers 8

# Minimize corpus
protocrash corpus minimize ./corpus --output ./corpus_min

# Use tmpfs for speed
mkdir -p /tmp/protocrash_corpus
cp -r ./corpus/* /tmp/protocrash_corpus/
protocrash fuzz --target ./app --corpus /tmp/protocrash_corpus
```

### Target not starting

**Causes:**
1. Wrong target path
2. Missing dependencies
3. Permission issues

**Solutions:**
```bash
# Verify target exists
ls -la ./target

# Make executable
chmod +x ./target

# Test manually
./target < corpus/seed1.txt
```

### Memory issues

**Error:** `MemoryError` or `Killed`

**Solutions:**
```bash
# Reduce workers
protocrash fuzz --target ./app --workers 2

# Set memory limit
protocrash fuzz --target ./app --memory-limit 512M

# Monitor memory
watch -n 1 free -h
```

---

## Analysis Issues

### No crashes in directory

**Error:** `No crash files found in ./crashes`

**Solutions:**
```bash
# Check directory exists
ls -la ./crashes

# Check file format
file ./crashes/*

# Verify crashes were saved
protocrash fuzz --target ./app --crashes ./crashes
ls -la ./crashes
```

### Classification fails

**Error:** `Cannot classify crash`

**Solutions:**
```bash
# Ensure crash has stack trace
cat ./crashes/crash_001.stderr

# Run with debug
PROTOCRASH_DEBUG=1 protocrash analyze --crash-dir ./crashes --classify
```

---

## Report Issues

### HTML report empty

**Causes:**
1. No stats collected
2. Wrong campaign directory

**Solutions:**
```bash
# Check campaign directory structure
ls -la ./campaign
# Should contain: corpus/, crashes/, stats.json

# Verify stats exist
cat ./campaign/stats.json
```

### Charts not rendering

**Causes:**
1. No internet (CDN charts)
2. JavaScript disabled

**Solutions:**
- Ensure internet access for Chart.js CDN
- Open HTML in modern browser
- Check browser console for errors

---

## Distributed Fuzzing Issues

### Workers not starting

**Causes:**
1. Multiprocessing issues
2. Resource exhaustion

**Solutions:**
```bash
# Reduce worker count
protocrash fuzz --target ./app --workers 2

# Check system limits
ulimit -a

# Increase file limits
ulimit -n 65535
```

### Corpus sync issues

**Solutions:**
```bash
# Check sync directory
ls -la /tmp/protocrash_sync_*/

# Increase sync interval
# In code: sync_interval=10.0
```

---

## Platform-Specific Issues

### Linux

**Missing ptrace permissions:**
```bash
# Allow ptrace
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
```

### Windows

**No keyboard controls:**
```bash
# Use non-interactive mode
protocrash fuzz --target ./app --no-dashboard
```

---

## Debug Mode

Enable detailed logging:

```bash
# Environment variable
PROTOCRASH_DEBUG=1 protocrash fuzz --target ./app

# Verbose flag
protocrash fuzz --target ./app --verbose
```

---

## Getting Help

1. Check documentation: `protocrash --help`
2. View logs: Check stderr output
3. GitHub issues: Report bugs with reproducible steps
4. Include: Python version, OS, command used, error message
