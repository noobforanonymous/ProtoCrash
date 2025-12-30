# AFL Bitmap Implementation - Technical Deep Dive

## Overview

American Fuzzy Lop (AFL) uses a 64KB shared-memory bitmap for coverage feedback. This document provides detailed technical insights into how AFL tracks coverage and guides fuzzing.

---

## 1. Core Concept: Edge Coverage

**Why Edge Coverage?**
- More granular than basic block coverage
- Captures control flow transitions
- Detects different execution paths

**Edge Definition:**
```
Edge = Transition from Block A → Block B
```

**Example:**
```c
if (x > 0) {    // Block A
    foo();      // Block B
} else {
    bar();      // Block C
}

Edges:
- A → B (when x > 0)
- A → C (when x <= 0)
```

---

## 2. Instrumentation

### Compile-Time Instrumentation

**AFL inserts code at every branch:**

```c
// Original code
if (condition) {
    foo();
} else {
    bar();
}

// After AFL instrumentation
cur_location = RANDOM_ID_1;
shared_mem[cur_location ^ prev_location]++;
prev_location = cur_location >> 1;

if (condition) {
    cur_location = RANDOM_ID_2;
    shared_mem[cur_location ^ prev_location]++;
    prev_location = cur_location >> 1;
    
    foo();
} else {
    cur_location = RANDOM_ID_3;
    shared_mem[cur_location ^ prev_location]++;
    prev_location = cur_location >> 1;
    
    bar();
}
```

### Random ID Assignment

**Each basic block gets a random 2-byte ID:**
```c
#define RANDOM_ID_1 0x1A2B
#define RANDOM_ID_2 0x3C4D
#define RANDOM_ID_3 0x5E6F
```

**Why Random?**
- Avoid collision patterns
- Distribute edges across bitmap
- Simple and fast

---

## 3. Bitmap Structure

### Size and Layout

```
Bitmap Size: 64KB (65536 bytes)
Address Range: 0x0000 - 0xFFFF

Each byte: Hit counter for one edge tuple
```

### Edge Hashing

**Formula:**
```c
edge_id = current_block_id ^ previous_block_id
bitmap_index = edge_id % 65536
```

**XOR Properties:**
- A → B produces different value than B → A
- Same blocks in different order = different edges
- Fast computation

**Example:**
```c
Block sequence: A → B → C

Edge 1: A → B
    edge_id = ID_A ^ ID_B
    index_1 = (0x1A2B ^ 0x3C4D) % 65536 = 0x2666

Edge 2: B → C
    edge_id = ID_B ^ ID_C
    index_2 = (0x3C4D ^ 0x5E6F) % 65536 = 0x6222
```

---

## 4. Hit Count Buckets

### Why Buckets?

**Problem:** Exact hit counts cause too much noise
**Solution:** Group counts into buckets

### Bucket Ranges

```c
Bucket 0: 0 hits (never executed)
Bucket 1: 1 hit
Bucket 2: 2 hits
Bucket 3: 3 hits
Bucket 4: 4-7 hits
Bucket 5: 8-15 hits
Bucket 6: 16-31 hits
Bucket 7: 32-127 hits
Bucket 8: 128+ hits
```

### Implementation

```c
static inline u8 count_class_lookup[256] = {
    [0] = 0,
    [1] = 1,
    [2] = 2,
    [3] = 3,
    [4 ... 7] = 4,
    [8 ... 15] = 5,
    [16 ... 31] = 6,
    [32 ... 127] = 7,
    [128 ... 255] = 8
};

u8 classify_counts(u8 count) {
    return count_class_lookup[count];
}
```

### Why This Matters

**Detects loop depth:**
```c
// Input 1: Loop runs 1 time → Bucket 1
// Input 2: Loop runs 5 times → Bucket 4
// Input 3: Loop runs 20 times → Bucket 6
```

Each is "interesting" because it reaches new bucket!

---

## 5. Coverage Comparison

### Detecting New Coverage

**Algorithm:**
```c
bool has_new_coverage(u8 *virgin_map, u8 *trace_bits) {
    u64 *virgin = (u64 *)virgin_map;
    u64 *current = (u64 *)trace_bits;
    
    for (u32 i = 0; i < MAP_SIZE / 8; i++) {
        if (current[i] && (current[i] & virgin[i])) {
            // Found new coverage
            return true;
        }
    }
    
    return false;
}
```

**Virgin Map:**
- Bitmap of unseen edges
- Bit set = edge not yet hit
- Bit clear = edge already seen

**Comparison:**
```
virgin_map:   11111111 11110000 00000000
current_exec: 00000001 00000100 00000010
                  ^        ^        ^
                new!     new!    new!
```

---

## 6. Hash Collisions

### Problem

**Different edges map to same bitmap index:**
```c
Edge A→B: hash(0x1234 ^ 0x5678) % 65536 = 1000
Edge C→D: hash(0xABCD ^ 0xEF01) % 65536 = 1000

Both write to bitmap[1000]!
```

### Impact

- Can't distinguish between different edges
- May miss unique coverage
- False "already seen" detections

### Mitigation Strategies

1. **Larger Bitmap:**
   - 128KB, 256KB, 1MB
   - Trade memory for accuracy

2. **Better Hashing:**
   - Two-level hashing (BigMap project)
   - Cryptographic hash functions

3. **Accept Trade-off:**
   - AFL chooses 64KB for L2 cache fit
   - Collisions rare enough in practice

---

## 7. Shared Memory

### Setup

**Fuzzer creates shared memory:**
```c
int shm_id = shmget(IPC_PRIVATE, MAP_SIZE, IPC_CREAT | 0600);
u8 *trace_bits = shmat(shm_id, NULL, 0);

// Pass ID to target via environment
setenv("__AFL_SHM_ID", shm_id_str, 1);
```

**Target attaches:**
```c
char *id_str = getenv("__AFL_SHM_ID");
int shm_id = atoi(id_str);
u8 *trace_bits = shmat(shm_id, NULL, 0);
```

### Performance

**Why Shared Memory?**
- Zero-copy data transfer
- Fast IPC between fuzzer and target
- Fuzzer reads bitmap instantly after execution

---

## 8. Coverage-Guided Fuzzing Loop

### Main Loop

```c
while (fuzzing) {
    // 1. Select input from queue
    input = queue.next();
    
    // 2. Clear bitmap
    memset(trace_bits, 0, MAP_SIZE);
    
    // 3. Execute target with input
    run_target(input);
    
    // 4. Check for new coverage
    has_new = has_new_coverage(virgin_map, trace_bits);
    
    if (has_new) {
        // 5. Mark edges as seen
        update_virgin_map(virgin_map, trace_bits);
        
        // 6. Add to corpus
        queue.add(input);
        
        // 7. Mark for more mutations
        input.favored = true;
    }
    
    // 8. Check for crash
    if (crashed) {
        save_crash(input);
    }
}
```

---

## 9. Optimization Tricks

### Fast Bitmap Comparison

**64-bit chunks:**
```c
u64 *virgin_64 = (u64 *)virgin_map;
u64 *trace_64 = (u64 *)trace_bits;

for (i = 0; i < MAP_SIZE / 8; i++) {
    if (trace_64[i] && (trace_64[i] & virgin_64[i])) {
        return HAS_NEW_COVERAGE;
    }
}
```

**Why?** Process 8 bytes at once (8x faster)

### Calibration Stage

**Initial run to establish baseline:**
```c
// Run input 8 times
for (i = 0; i < 8; i++) {
    run_target(input);
    record_coverage();
}

// Calculate stability
if (coverage_stable) {
    input.favored = true;
} else {
    input.favored = false;  // Non-deterministic
}
```

---

## 10. Practical Implementation for ProtoCrash

### Coverage Tracker Class

```python
import mmap
import os

class CoverageMap:
    MAP_SIZE = 65536  # 64KB like AFL
    
    def __init__(self):
        self.bitmap = bytearray(self.MAP_SIZE)
        self.virgin_map = bytearray([0xFF] * self.MAP_SIZE)  # All unseen
        self.prev_location = 0
    
    def reset(self):
        """Clear bitmap for new execution"""
        self.bitmap = bytearray(self.MAP_SIZE)
        self.prev_location = 0
    
    def record_edge(self, current_location: int):
        """Record edge execution (called by instrumentation)"""
        edge_id = current_location ^ self.prev_location
        index = edge_id % self.MAP_SIZE
        
        # Increment hit counter (with saturation)
        if self.bitmap[index] < 255:
            self.bitmap[index] += 1
        
        # Update previous location for next edge
        self.prev_location = current_location >> 1
    
    def has_new_coverage(self) -> bool:
        """Check if current execution found new coverage"""
        for i in range(self.MAP_SIZE):
            if self.bitmap[i] and (self.bitmap[i] & self.virgin_map[i]):
                return True
        return False
    
    def update_virgin(self):
        """Mark current coverage as seen"""
        for i in range(self.MAP_SIZE):
            self.virgin_map[i] &= ~self.bitmap[i]
```

---

## Performance Metrics

**AFL Typical Performance:**
- Execution Rate: 100-1000 execs/sec
- Coverage Overhead: < 10%
- Bitmap Comparison: < 1ms
- Memory Usage: 64KB + target memory

**ProtoCrash Target:**
- Execution Rate: 100-500 execs/sec
- Coverage Overhead: < 15%
- Support for Python-based tracking

---

Status: AFL bitmap implementation documentation complete
