# Day 2 - Research & Protocol Analysis

**Phase:** Foundation  
**Focus:** Coverage-guided fuzzing techniques and protocol vulnerabilities

---

## Goals Completed

- Researched AFL bitmap implementation details
- Studied coverage-guided fuzzing algorithms
- Analyzed HTTP protocol fuzzing vulnerabilities
- Researched DNS protocol attack patterns
- Documented fuzzing techniques

---

## Research Findings

### 1. AFL Bitmap Implementation

**Core Concept:**
- AFL uses a 64KB shared-memory bitmap for coverage feedback
- Tracks **edge coverage** (branch transitions) not just basic blocks
- Each byte in bitmap represents unique execution flow tuple

**How It Works:**
```python
# Pseudocode for AFL edge tracking
current_block_id = random_id()
previous_block_id = get_previous()

# Create unique edge identifier
edge_id = current_block_id ^ previous_block_id

# Hash to bitmap offset
bitmap_index = hash(edge_id) % BITMAP_SIZE

# Increment hit counter (bucketed)
bitmap[bitmap_index]++
```

**Hit Count Buckets:**
- Not storing exact counts, use buckets: `{1, 2, 3, 4-7, 8-15, 16-31, 32-127, 128+}`
- Reduces 256 possible values to ~9 buckets
- Enables efficient novelty detection with bitwise operations

**Key Insights:**
- Edge coverage more granular than basic block coverage
- Hit count buckets help identify deep execution paths (loops)
- Hash collisions are a challenge (different edges → same bitmap offset)
- 64KB chosen for L2 cache optimization

---

### 2. Coverage-Guided Fuzzing Techniques

**Feedback Loop:**
```
1. Select input from corpus
2. Mutate input
3. Execute target
4. Collect coverage bitmap
5. Compare with previous coverage
6. If new coverage → add to corpus
7. If crash → save to crashes
8. Repeat
```

**"Interesting" Input Criteria:**
- Hits new edge (previously unseen transition)
- Reaches new hit count bucket on existing edge
- Triggers deeper execution (higher loop iterations)

**Mutation Strategies:**
- **Bit flips:** Single-bit corruption
- **Byte flips:** Multi-byte corruption  
- **Arithmetic:** Add/subtract small values
- **Dictionary:** Inject known keywords
- **Havoc:** Random chaotic mutations
- **Splice:** Combine two corpus inputs

**Queue Scheduling:**
- Prefer smaller inputs (faster execution)
- Favor recent additions (fresh coverage)
- Weight by coverage density
- Occasional random selection

---

### 3. HTTP Protocol Vulnerabilities

**Common Bug Classes:**

1. **Buffer Overflows**
   - Occur when receiving more data than buffer can handle
   - Target: Headers, query parameters, POST body
   - Detection: Long strings, incremented field lengths
   - Example: `GET /` + "A" * 10000 + ` HTTP/1.1`

2. **Injection Attacks**
   - SQL Injection: `' OR '1'='1`
   - Command Injection: `; ls -la`
   - Header Injection: `\r\nSet-Cookie: malicious=1`
   - NoSQL Injection: `{"$ne": null}`

3. **HTTP/2 Specific**
   - Flow control violations
   - Stream multiplexing edge cases
   - HPACK header compression bugs

4. **Logic Bugs**
   - Unexpected request combinations
   - Invalid state transitions
   - Malformed content-length vs actual body

**Fuzzing Target Points:**
- HTTP method (GET, POST, PUT, DELETE, custom)
- URI path (length, special characters, encoding)
- HTTP version (1.0, 1.1, 2.0, invalid)
- Headers (custom, duplicates, oversized)
- Query parameters (special chars, injection)
- POST/PUT body (size, format, encoding)

---

### 4. DNS Protocol Vulnerabilities

**Common Attack Patterns:**

1. **Cache Poisoning**
   - Inject forged DNS records into resolver cache
   - Redirect users to malicious sites
   - Found via fuzzing query-response sequences

2. **DNS Amplification/Reflection DDoS**
   - Exploit open resolvers to amplify attack traffic
   - Small query → large response to victim
   - Target: Query type (ANY), DNSSEC records

3. **DNS Tunneling**
   - Encapsulate data in DNS queries/responses
   - Bypass firewalls and exfiltrate data
   - Fuzzing reveals protocol handling weaknesses

4. **Resource Exhaustion**
   - NXDOMAIN floods (non-existent domains)
   - Malformed packets consuming CPU/memory
   - Protocol-level DoS

**DNS Fuzzing Targets:**
- Query ID (random, duplicate, sequential)
- Query type (A, AAAA, MX, TXT, ANY, invalid codes)
- Query class (IN, CH, HS, invalid)
- Query name (length, labels, encoding, compression pointers)
- Flags (QR, AA, TC, RD, RA, Z, RCODE)
- Additional records (OPT, EDNS0)
- Packet structure (truncated, oversized, nested compression)

---

## Protocol Cheat Sheets Created

### HTTP Request Structure
```
METHOD /path?param=value HTTP/VERSION
Host: domain.com
Header-Name: Header-Value
Content-Length: 123

Request Body (if POST/PUT)
```

**Fuzzing Strategy:**
- Vary method length and characters
- Inject special chars in path: `%00`, `../`, `//`
- Invalid HTTP versions: `HTTP/0.0`, `HTTP/99.9`
- Duplicate headers
- Mismatch Content-Length with actual body

### DNS Packet Structure
```
Header: ID(2) | Flags(2) | QDCOUNT(2) | ANCOUNT(2) | NSCOUNT(2) | ARCOUNT(2)
Question: QNAME(variable) | QTYPE(2) | QCLASS(2)
Answer: NAME(variable) | TYPE(2) | CLASS(2) | TTL(4) | RDLENGTH(2) | RDATA(variable)
```

**Fuzzing Strategy:**
- Invalid QTYPE values (beyond standard types)
- Malformed QNAME (invalid labels, compression loops)
- Oversized RDLENGTH
- Truncated packets
- Invalid flag combinations

---

## Coverage Tracking Design for ProtoCrash

**Implementation Plan:**

```python
class CoverageMap:
    def __init__(self):
        self.bitmap = bytearray(65536)  # 64KB like AFL
        self.edges_found = set()
        self.hit_buckets = {}
    
    def record_edge(self, edge_id: int):
        # Hash edge to bitmap index
        index = edge_id % len(self.bitmap)
        
        # Increment hit counter (bucketed)
        current = self.bitmap[index]
        if current < 255:
            self.bitmap[index] += 1
    
    def has_new_coverage(self, previous_bitmap) -> bool:
        # Compare bitmaps for new edges or hit counts
        for i in range(len(self.bitmap)):
            if self.bitmap[i] > 0 and previous_bitmap[i] == 0:
                return True  # New edge
            if self._get_bucket(self.bitmap[i]) != self._get_bucket(previous_bitmap[i]):
                return True  # New hit count bucket
        return False
    
    def _get_bucket(self, count: int) -> int:
        # AFL-style hit count buckets
        if count == 0: return 0
        if count == 1: return 1
        if count == 2: return 2
        if count == 3: return 3
        if count <= 7: return 4
        if count <= 15: return 5
        if count <= 31: return 6
        if count <= 127: return 7
        return 8
```

---

## Mutation Engine Design

**Mutation Priorities:**

1. **Deterministic Mutations** (low entropy, systematic):
   - Bit flips: 1/1, 2/1, 4/1
   - Byte flips: 8/8, 16/8, 32/8
   - Arithmetics: +1, -1, +MAX, -MAX

2. **Havoc Mutations** (high entropy, random):
   - Random bit/byte flips
   - Block deletions/insertions
   - Random overwrites

3. **Dictionary-Based** (protocol-aware):
   - HTTP keywords: GET, POST, Content-Length
   - DNS keywords: query types, response codes
   - Common injection payloads

4. **Splicing** (combining inputs):
   - Take head of corpus_input_1
   - Take tail of corpus_input_2
   - Combine and mutate

---

## Next Steps

**Day 3-5: Architecture Refinement**
- Finalize mutation engine implementation
- Design coverage tracker with bitmap
- Plan crash detector (signal handling)
- Create protocol parser interfaces
- Document component specifications

**Immediate Tasks:**
- Create detailed architecture diagrams
- Write mutation engine specification
- Design protocol parser API
- Plan target executor architecture

---

## Lessons Learned

1. **Edge coverage > basic block coverage** - More granular path tracking
2. **Hit count buckets are critical** - Identify deep paths (loops)
3. **Hash collisions matter** - Need large enough bitmap
4. **Protocol-aware mutations work better** - Generic fuzzing misses bugs
5. **Query-response sequences** - Critical for DNS/HTTP fuzzing

---

## Technical Notes

### Performance Considerations
- Bitmap comparison should be fast (bitwise ops)
- Minimize fuzzing loop overhead (< 10%)
- Use shared memory for coverage tracking
- Cache corpus inputs for quick access

### Protocol Handling
- Need grammar-based parsers for binary protocols
- HTTP/DNS have standard libraries (scapy, dpkt)
- Custom protocols need user-defined grammar
- Auto-fix length/checksum fields

---

## Code Changes

**Files Created:**
- research/day02_fuzzing_techniques.md (this file)
- research/afl_bitmap_notes.md (technical deep dive)
- research/protocol_vulns.md (vulnerability patterns)

**Research Artifacts:**
- AFL bitmap implementation notes
- Coverage-guided fuzzing algorithm
- HTTP/DNS protocol cheat sheets
- Mutation strategy catalog

---

Status: Research phase complete, moving to architecture refinement
