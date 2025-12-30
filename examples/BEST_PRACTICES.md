# ProtoCrash Best Practices Guide

Guidelines for effective fuzzing with ProtoCrash.

---

## Corpus Management

### Start with Valid Inputs
- Use real, valid protocol messages as seeds
- Include diverse message types and formats
- Extract samples from network captures (pcap)

```bash
# Generate initial corpus
python3 examples/scripts/generate_corpus.py -o ./corpus --protocol http
```

### Keep Corpus Small
- Remove redundant inputs regularly
- Quality > quantity
- 10-100 well-chosen seeds often beats 10,000 random ones

### Organize by Category
```
corpus/
├── valid/          # Valid protocol messages
├── edge_cases/     # Boundary conditions
├── malformed/      # Known error cases
└── interesting/    # Discovered inputs
```

---

## Mutation Strategy

### Match Protocol Structure
- Use protocol-specific mutators (http, dns, binary)
- Define grammars for binary protocols
- Include protocol keywords in dictionaries

### Dictionary Usage
```bash
# Create protocol dictionary
cat > keywords.txt << EOF
GET
POST
HTTP/1.1
Content-Length
Authorization
../../../etc/passwd
%s%s%s%s
EOF

protocrash fuzz --target ./app --dictionary keywords.txt
```

---

## Performance Optimization

### Parallel Workers
```bash
# Use all CPU cores
protocrash fuzz --target ./app --workers $(nproc)
```

### Timeout Tuning
- Start with 5000ms (5 seconds)
- Lower for faster apps: 1000ms
- Higher for slow apps: 10000ms

### Memory Management
```bash
# Limit memory per process
protocrash fuzz --target ./app --memory-limit 512M
```

### Use RAM Disk
```bash
# For faster I/O
mkdir -p /dev/shm/protocrash_corpus
cp -r corpus/* /dev/shm/protocrash_corpus/
protocrash fuzz --corpus /dev/shm/protocrash_corpus
```

---

## Crash Analysis

### Triage First
1. Deduplicate crashes
2. Group by root cause
3. Prioritize by exploitability

### Minimize Inputs
- Smaller inputs are easier to analyze
- Help identify root cause faster

### Document Findings
```bash
# Create crash report directory
for crash in crashes/*.bin; do
  base=$(basename "$crash" .bin)
  mkdir -p "reports/$base"
  cp "$crash" "reports/$base/"
  protocrash analyze --crash-dir "reports/$base" > "reports/$base/analysis.txt"
done
```

---

## Integration

### CI/CD Pipeline
- Run fuzzing on every PR
- Set time limits (5-10 minutes)
- Fail build on crashes
- Archive crash artifacts

### Scheduled Fuzzing
- Run extended campaigns nightly
- Use distributed fuzzing for coverage
- Review crashes daily

---

## Common Pitfalls

### Avoid These Mistakes

1. **Too short timeout** - Miss slow bugs
2. **Too long timeout** - Waste CPU cycles
3. **No seed corpus** - Poor coverage
4. **Ignoring crashes** - Missing vulnerabilities
5. **Single worker** - Underutilizing resources

### Signs of Good Fuzzing

- Steady exec/sec rate
- Coverage increasing over time
- Unique crashes being found
- Corpus growing (slowly)
