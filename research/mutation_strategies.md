# Mutation Strategies - Deep Dive

## Overview

Mutation fuzzing is a testing technique that modifies existing valid inputs (seeds) to create malformed test cases that expose vulnerabilities. This document provides comprehensive coverage of mutation strategies used in modern coverage-guided fuzzers.

---

## 1. Deterministic Mutations

Deterministic mutations are applied systematically at every position in the input. AFL uses this approach for thoroughness.

### 1.1 Bit Flips

**Description:** Invert specific bits within the input data.

**Strategies:**
- **1/1:** Flip single bits (walk through each bit)
- **2/1:** Flip 2 consecutive bits
- **4/1:** Flip 4 consecutive bits (half a byte)

**Example:**
```python
original = 0b01000001  # 'A' (65)
flip_bit_0 = 0b01000000  # '@' (64)
flip_bit_6 = 0b00000001  # (1)
```

**Use Case:** Detect off-by-one errors, boundary conditions, bitwise operation bugs

**Implementation:**
```python
def bit_flip(data: bytes, position: int, count: int = 1) -> bytes:
    """Flip 'count' bits starting at 'position'"""
    result = bytearray(data)
    byte_idx = position // 8
    bit_idx = position % 8
    
    for i in range(count):
        if byte_idx < len(result):
            result[byte_idx] ^= (1 << bit_idx)
            bit_idx += 1
            if bit_idx >= 8:
                bit_idx = 0
                byte_idx += 1
    
    return bytes(result)
```

---

### 1.2 Byte Flips

**Description:** Modify entire bytes within the input.

**Strategies:**
- **8/8:** Flip single bytes (XOR with 0xFF)
- **16/8:** Flip 2 consecutive bytes
- **32/8:** Flip 4 consecutive bytes

**Boundary Values:**
- Replace with 0x00 (null byte)
- Replace with 0xFF (max byte)
- Replace with 0x7F / 0x80 (sign bit boundary)

**Implementation:**
```python
def byte_flip(data: bytes, position: int, count: int = 1) -> bytes:
    """Flip 'count' bytes starting at 'position'"""
    result = bytearray(data)
    for i in range(count):
        if position + i < len(result):
            result[position + i] ^= 0xFF
    return bytes(result)

def replace_boundary_byte(data: bytes, position: int, value: int) -> bytes:
    """Replace byte at 'position' with boundary value"""
    result = bytearray(data)
    if position < len(result):
        result[position] = value
    return bytes(result)
```

---

### 1.3 Arithmetic Mutations

**Description:** Add/subtract small integers to numeric fields.

**Strategies:**
- Increment/decrement by 1
- Add/subtract 8, 16, 32 (common integer sizes)
- Test integer overflows (add to MAX_INT)

**Interesting Values:**
```python
INTERESTING_8 = [
    -128, -1, 0, 1, 16, 32, 64, 100, 127
]

INTERESTING_16 = [
    -32768, -129, 128, 255, 256, 512, 1000, 1024, 4096, 32767
]

INTERESTING_32 = [
    -2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647
]
```

**Implementation:**
```python
def arithmetic_mutate(data: bytes, position: int, delta: int, size: int = 1) -> bytes:
    """Add 'delta' to integer at 'position' of 'size' bytes"""
    result = bytearray(data)
    
    # Extract current value
    if position + size > len(result):
        return bytes(result)
    
    value = int.from_bytes(result[position:position+size], 'little')
    
    # Apply arithmetic
    new_value = (value + delta) % (256 ** size)
    
    # Write back
    result[position:position+size] = new_value.to_bytes(size, 'little')
    
    return bytes(result)
```

---

## 2. Havoc Mutations

Havoc is a highly randomized mutation stage that stacks multiple mutations.

**Mutation Stack:**
```
Input → Random Mutation 1 → Random Mutation 2 → ... → Output
```

**Havoc Operations:**
1. **Random Byte Flips:** Flip random single byte
2. **Random Bit Flips:** Flip random single bit
3. **Interesting Value:** Replace byte with interesting value
4. **Arithmetic:** Add/subtract random small integer
5. **Block Delete:** Remove random chunk of input
6. **Block Duplicate:** Copy and insert random chunk
7. **Block Swap:** Swap two random chunks
8. **Random Overwrite:** Overwrite random bytes with random data

**Algorithm:**
```python
def havoc_mutate(data: bytes, iterations: int = 10) -> bytes:
    """Apply random sequence of mutations"""
    result = data
    
    for _ in range(iterations):
        mutation_type = random.choice([
            'flip_bit', 'flip_byte', 'arithmetic',
            'interesting', 'delete_block', 'duplicate_block',
            'swap_blocks', 'random_overwrite'
        ])
        
        if mutation_type == 'flip_bit':
            pos = random.randint(0, len(result) * 8 - 1)
            result = bit_flip(result, pos)
        
        elif mutation_type == 'flip_byte':
            pos = random.randint(0, len(result) - 1)
            result = byte_flip(result, pos)
        
        elif mutation_type == 'arithmetic':
            pos = random.randint(0, len(result) - 1)
            delta = random.randint(-35, 35)
            result = arithmetic_mutate(result, pos, delta)
        
        elif mutation_type == 'delete_block':
            if len(result) > 2:
                start = random.randint(0, len(result) - 2)
                end = random.randint(start + 1, len(result))
                result = result[:start] + result[end:]
        
        elif mutation_type == 'duplicate_block':
            if len(result) > 2:
                start = random.randint(0, len(result) - 2)
                end = random.randint(start + 1, len(result))
                block = result[start:end]
                insert_pos = random.randint(0, len(result))
                result = result[:insert_pos] + block + result[insert_pos:]
        
        # ... other mutations
    
    return result
```

---

## 3. Dictionary-Based Mutations

**Description:** Inject protocol-specific keywords and common attack strings.

**Dictionary Categories:**

**HTTP Keywords:**
```
GET
POST
PUT
DELETE
HTTP/1.0
HTTP/1.1
Content-Length
Transfer-Encoding
chunked
Host
Authorization
```

**SQL Injection:**
```
' OR '1'='1
' OR 1=1--
'; DROP TABLE users--
UNION SELECT NULL--
```

**Command Injection:**
```
; ls -la
| whoami
`id`
$(cat /etc/passwd)
```

**Implementation:**
```python
def dictionary_inject(data: bytes, dictionary: List[bytes], position: int = None) -> bytes:
    """Inject dictionary token into input"""
    token = random.choice(dictionary)
    
    if position is None:
        position = random.randint(0, len(data))
    
    return data[:position] + token + data[position:]

def dictionary_replace(data: bytes, dictionary: List[bytes], start: int, end: int) -> bytes:
    """Replace range with dictionary token"""
    token = random.choice(dictionary)
    return data[:start] + token + data[end:]
```

---

## 4. Splice/Crossover Mutations

**Description:** Combine two corpus inputs to create new test cases.

**Algorithm:**
```python
def splice_inputs(input1: bytes, input2: bytes) -> bytes:
    """Combine two inputs via crossover"""
    if len(input1) < 2 or len(input2) < 2:
        return input1
    
    # Choose split points
    split1 = random.randint(1, len(input1) - 1)
    split2 = random.randint(1, len(input2) - 1)
    
    # Combine head of input1 with tail of input2
    result = input1[:split1] + input2[split2:]
    
    return result
```

**Use Case:** Combine interesting features from different test cases

---

## 5. Structure-Aware Mutations

**Description:** Respect protocol grammar during mutations.

**Binary Protocol Example:**
```python
class ProtocolMutator:
    def __init__(self, grammar):
        self.grammar = grammar
    
    def mutate_field(self, data: bytes, field_name: str) -> bytes:
        """Mutate specific protocol field"""
        field_def = self.grammar.get_field(field_name)
        field_offset = field_def['offset']
        field_size = field_def['size']
        
        # Extract field value
        field_value = data[field_offset:field_offset + field_size]
        
        # Mutate based on field type
        if field_def['type'] == 'length':
            # For length fields, try boundary values
            mutated = self._mutate_length(field_value, field_size)
        elif field_def['type'] == 'enum':
            # For enums, try invalid values
            mutated = self._mutate_enum(field_value, field_def['valid_values'])
        else:
            # Generic mutation
            mutated = havoc_mutate(field_value, iterations=1)
        
        # Reassemble packet
        return data[:field_offset] + mutated + data[field_offset + field_size:]
    
    def fix_checksums(self, data: bytes) -> bytes:
        """Recalculate checksums after mutation"""
        # Implementation depends on protocol
        pass
```

---

## 6. Mutation Scheduling

**Coverage-Guided Strategy:**
```python
def select_mutation_strategy(input_history: Dict) -> str:
    """Choose mutation based on past effectiveness"""
    strategies = ['deterministic', 'havoc', 'dictionary', 'splice']
    weights = []
    
    for strategy in strategies:
        # Weight by past coverage gains
        coverage_gain = input_history.get(f'{strategy}_coverage', 0)
        weights.append(coverage_gain + 1)  # +1 to avoid zero weight
    
    return random.choices(strategies, weights=weights)[0]
```

---

## Performance Considerations

1. **Deterministic first:** Exhaustive but systematic
2. **Havoc for deep paths:** Random exploration
3. **Dictionary for protocols:** Target specific bugs
4. **Splice for diversity:** Combine successful features

**Mutation Budget:**
- Deterministic: ~1000 mutations per input
- Havoc: ~100-500 iterations
- Dictionary: ~50-100 injections
- Splice: ~10-20 combinations

---

Status: Comprehensive mutation strategy documentation complete
