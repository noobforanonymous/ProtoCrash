# Mutation Engine - Component Specification

## Overview

The mutation engine applies intelligent mutations to inputs to generate new test cases. Based on AFL-style deterministic and havoc strategies with protocol-aware enhancements.

---

## Architecture

```
┌─────────────────────────────────────────┐
│         Mutation Engine                 │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐   ┌──────────────┐   │
│  │ Deterministic│   │    Havoc     │   │
│  │  Mutators    │   │   Mutators   │   │
│  └──────────────┘   └──────────────┘   │
│         │                   │           │
│         ▼                   ▼           │
│  ┌──────────────────────────────────┐  │
│  │     Mutation Scheduler           │  │
│  └──────────────────────────────────┘  │
│         │                               │
│         ▼                               │
│  ┌──────────────────────────────────┐  │
│  │     Dictionary Manager           │  │
│  └──────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

---

## Class Design

### 1. MutationEngine (Main Class)

```python
from typing import List, Dict, Optional
from dataclasses import dataclass
import random

@dataclass
class MutationConfig:
    """Configuration for mutation engine"""
    deterministic_enabled: bool = True
    havoc_enabled: bool = True
    dictionary_enabled: bool = True
    splice_enabled: bool = True
    
    # Mutation budgets
    deterministic_iterations: int = 1000
    havoc_iterations: int = 200
    splice_attempts: int = 10
    
    # Weights for mutation selection
    mutation_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.mutation_weights is None:
            self.mutation_weights = {
                'bit_flip': 0.2,
                'byte_flip': 0.15,
                'arithmetic': 0.15,
                'interesting': 0.1,
                'havoc': 0.25,
                'dictionary': 0.1,
                'splice': 0.05
            }

class MutationEngine:
    """Main mutation engine coordinator"""
    
    def __init__(self, config: MutationConfig = None):
        self.config = config or MutationConfig()
        
        # Initialize mutators
        self.deterministic = DeterministicMutator()
        self.havoc = HavocMutator()
        self.dictionary = DictionaryManager()
        self.splice = SpliceMutator()
        
        # Track mutation effectiveness
        self.mutation_stats = {}
    
    def mutate(self, input_data: bytes, strategy: str = 'auto') -> bytes:
        """Main mutation entry point"""
        if strategy == 'auto':
            strategy = self._select_strategy()
        
        if strategy == 'deterministic':
            return self._mutate_deterministic(input_data)
        elif strategy == 'havoc':
            return self.havoc.mutate(input_data)
        elif strategy == 'dictionary':
            return self.dictionary.inject(input_data)
        elif strategy == 'splice':
            return self.splice.crossover(input_data, self._get_random_corpus())
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def mutate_batch(self, input_data: bytes, count: int) -> List[bytes]:
        """Generate multiple mutations"""
        mutations = []
        for _ in range(count):
            mutations.append(self.mutate(input_data))
        return mutations
    
    def _select_strategy(self) -> str:
        """Select mutation strategy based on weights"""
        strategies = list(self.config.mutation_weights.keys())
        weights = list(self.config.mutation_weights.values())
        return random.choices(strategies, weights=weights)[0]
    
    def _mutate_deterministic(self, data: bytes) -> bytes:
        """Run deterministic mutation stage"""
        # Cycle through deterministic strategies
        mutations = []
        mutations.extend(self.deterministic.bit_flips(data))
        mutations.extend(self.deterministic.byte_flips(data))
        mutations.extend(self.deterministic.arithmetic(data))
        
        return random.choice(mutations) if mutations else data
    
    def update_effectiveness(self, strategy: str, found_coverage: bool):
        """Update mutation effectiveness tracking"""
        if strategy not in self.mutation_stats:
            self.mutation_stats[strategy] = {'attempts': 0, 'successes': 0}
        
        self.mutation_stats[strategy]['attempts'] += 1
        if found_coverage:
            self.mutation_stats[strategy]['successes'] += 1
            
            # Increase weight for successful strategy
            success_rate = (self.mutation_stats[strategy]['successes'] / 
                          self.mutation_stats[strategy]['attempts'])
            self.config.mutation_weights[strategy] *= (1 + success_rate * 0.1)
```

---

### 2. DeterministicMutator

```python
class DeterministicMutator:
    """Systematic deterministic mutations"""
    
    def bit_flips(self, data: bytes, positions: Optional[List[int]] = None) -> List[bytes]:
        """Generate all bit flip mutations"""
        mutations = []
        
        if positions is None:
            # Flip every bit
            for bit_pos in range(len(data) * 8):
                mutations.append(self._flip_bit(data, bit_pos))
        else:
            for pos in positions:
                mutations.append(self._flip_bit(data, pos))
        
        return mutations
    
    def _flip_bit(self, data: bytes, position: int) -> bytes:
        """Flip single bit at position"""
        result = bytearray(data)
        byte_idx = position // 8
        bit_idx = position % 8
        
        if byte_idx < len(result):
            result[byte_idx] ^= (1 << bit_idx)
        
        return bytes(result)
    
    def byte_flips(self, data: bytes, sizes: List[int] = [1, 2, 4]) -> List[bytes]:
        """Generate byte flip mutations"""
        mutations = []
        
        for size in sizes:
            for pos in range(len(data) - size + 1):
                mutations.append(self._flip_bytes(data, pos, size))
        
        return mutations
    
    def _flip_bytes(self, data: bytes, position: int, count: int) -> bytes:
        """Flip 'count' consecutive bytes"""
        result = bytearray(data)
        for i in range(count):
            if position + i < len(result):
                result[position + i] ^= 0xFF
        return bytes(result)
    
    def arithmetic(self, data: bytes, deltas: List[int] = None) -> List[bytes]:
        """Arithmetic mutations (add/subtract)"""
        if deltas is None:
            deltas = [-35, -1, 1, 8, 16, 32]
        
        mutations = []
        
        for pos in range(len(data)):
            for delta in deltas:
                for size in [1, 2, 4]:
                    if pos + size <= len(data):
                        mutations.append(self._arithmetic_mutate(data, pos, delta, size))
        
        return mutations
    
    def _arithmetic_mutate(self, data: bytes, pos: int, delta: int, size: int) -> bytes:
        """Add delta to integer at position"""
        result = bytearray(data)
        
        # Extract value
        value = int.from_bytes(result[pos:pos+size], 'little')
        
        # Apply arithmetic
        new_value = (value + delta) % (256 ** size)
        
        # Write back
        result[pos:pos+size] = new_value.to_bytes(size, 'little')
        
        return bytes(result)
    
    def interesting_values(self, data: bytes) -> List[bytes]:
        """Replace with AFL interesting values"""
        INTERESTING_8 = [-128, -1, 0, 1, 16, 32, 64, 100, 127]
        INTERESTING_16 = [-32768, -129, 128, 255, 256, 512, 1000, 1024, 4096, 32767]
        INTERESTING_32 = [-2147483648, -100663046, -32769, 32768, 65535, 65536, 2147483647]
        
        mutations = []
        
        for pos in range(len(data)):
            # 8-bit
            for val in INTERESTING_8:
                mutations.append(self._replace_int(data, pos, val, 1))
            
            # 16-bit
            if pos + 2 <= len(data):
                for val in INTERESTING_16:
                    mutations.append(self._replace_int(data, pos, val, 2))
            
            # 32-bit
            if pos + 4 <= len(data):
                for val in INTERESTING_32:
                    mutations.append(self._replace_int(data, pos, val, 4))
        
        return mutations
    
    def _replace_int(self, data: bytes, pos: int, value: int, size: int) -> bytes:
        """Replace integer at position"""
        result = bytearray(data)
        # Handle negative values
        if value < 0:
            value = (1 << (size * 8)) + value
        result[pos:pos+size] = value.to_bytes(size, 'little')
        return bytes(result)
```

---

### 3. HavocMutator

```python
import random

class HavocMutator:
    """Random havoc mutations"""
    
    HAVOC_OPERATIONS = [
        'flip_bit', 'flip_byte', 'arithmetic', 'interesting',
        'delete_block', 'clone_block', 'overwrite_block',
        'insert_random', 'shuffle_bytes'
    ]
    
    def mutate(self, data: bytes, iterations: int = 200) -> bytes:
        """Apply random sequence of mutations"""
        result = data
        
        for _ in range(iterations):
            op = random.choice(self.HAVOC_OPERATIONS)
            result = self._apply_operation(result, op)
        
        return result
    
    def _apply_operation(self, data: bytes, operation: str) -> bytes:
        """Apply single havoc operation"""
        if len(data) == 0:
            return data
        
        if operation == 'flip_bit':
            pos = random.randint(0, len(data) * 8 - 1)
            return self._flip_bit(data, pos)
        
        elif operation == 'flip_byte':
            pos = random.randint(0, len(data) - 1)
            result = bytearray(data)
            result[pos] ^= 0xFF
            return bytes(result)
        
        elif operation == 'arithmetic':
            if len(data) >= 1:
                pos = random.randint(0, len(data) - 1)
                delta = random.randint(-35, 35)
                return self._add_to_byte(data, pos, delta)
        
        elif operation == 'delete_block':
            if len(data) > 2:
                start = random.randint(0, len(data) - 2)
                end = random.randint(start + 1, len(data))
                return data[:start] + data[end:]
        
        elif operation == 'clone_block':
            if len(data) > 2:
                start = random.randint(0, len(data) - 2)
                end = random.randint(start + 1, len(data))
                block = data[start:end]
                insert_pos = random.randint(0, len(data))
                return data[:insert_pos] + block + data[insert_pos:]
        
        elif operation == 'overwrite_block':
            if len(data) > 2:
                start = random.randint(0, len(data) - 2)
                end = min(start + random.randint(1, 10), len(data))
                random_bytes = bytes([random.randint(0, 255) for _ in range(end - start)])
                return data[:start] + random_bytes + data[end:]
        
        return data
    
    def _flip_bit(self, data: bytes, position: int) -> bytes:
        """Flip single bit"""
        result = bytearray(data)
        byte_idx = position // 8
        bit_idx = position % 8
        if byte_idx < len(result):
            result[byte_idx] ^= (1 << bit_idx)
        return bytes(result)
    
    def _add_to_byte(self, data: bytes, pos: int, delta: int) -> bytes:
        """Add delta to byte"""
        result = bytearray(data)
        result[pos] = (result[pos] + delta) % 256
        return bytes(result)
```

---

### 4. DictionaryManager

```python
class DictionaryManager:
    """Manage mutation dictionaries"""
    
    def __init__(self):
        self.dictionaries = {
            'http': self._load_http_dict(),
            'dns': self._load_dns_dict(),
            'smtp': self._load_smtp_dict(),
            'sql': self._load_sql_dict(),
            'command': self._load_command_dict()
        }
    
    def inject(self, data: bytes, protocol: str = None) -> bytes:
        """Inject dictionary token into data"""
        if protocol and protocol in self.dictionaries:
            dict_words = self.dictionaries[protocol]
        else:
            # Use all dictionaries
            dict_words = []
            for words in self.dictionaries.values():
                dict_words.extend(words)
        
        if not dict_words:
            return data
        
        token = random.choice(dict_words)
        position = random.randint(0, len(data))
        
        return data[:position] + token + data[position:]
    
    def replace(self, data: bytes, start: int, end: int, protocol: str = None) -> bytes:
        """Replace range with dictionary token"""
        if protocol and protocol in self.dictionaries:
            dict_words = self.dictionaries[protocol]
        else:
            dict_words = []
            for words in self.dictionaries.values():
                dict_words.extend(words)
        
        if not dict_words:
            return data
        
        token = random.choice(dict_words)
        return data[:start] + token + data[end:]
    
    def _load_http_dict(self) -> List[bytes]:
        return [
            b'GET', b'POST', b'PUT', b'DELETE', b'HEAD', b'OPTIONS',
            b'HTTP/1.0', b'HTTP/1.1', b'HTTP/2.0',
            b'Host:', b'Content-Length:', b'Transfer-Encoding:',
            b'chunked', b'Authorization:', b'Cookie:',
            b'Accept:', b'User-Agent:', b'Referer:'
        ]
    
    def _load_dns_dict(self) -> List[bytes]:
        return [
            b'\x00\x01',  # A record
            b'\x00\x05',  # CNAME
            b'\x00\x0F',  # MX
            b'\x00\xFF',  # ANY
            b'\xC0\x0C',  # Compression pointer
        ]
    
    def _load_smtp_dict(self) -> List[bytes]:
        return [
            b'HELO', b'EHLO', b'MAIL FROM:', b'RCPT TO:',
            b'DATA', b'QUIT', b'RSET', b'HELP',
            b'\r\n', b'\r\n.\r\n'
        ]
    
    def _load_sql_dict(self) -> List[bytes]:
        return [
            b"' OR '1'='1", b"'; DROP TABLE", b"UNION SELECT",
            b"/*", b"*/", b"--", b"#"
        ]
    
    def _load_command_dict(self) -> List[bytes]:
        return [
            b'; ls', b'| whoami', b'`id`', b'$(cat /etc/passwd)',
            b'&& curl', b'|| wget'
        ]
```

---

### 5. SpliceMutator

```python
class SpliceMutator:
    """Splice/crossover mutations"""
    
    def crossover(self, input1: bytes, input2: bytes) -> bytes:
        """Combine two inputs"""
        if len(input1) < 2 or len(input2) < 2:
            return input1
        
        split1 = random.randint(1, len(input1) - 1)
        split2 = random.randint(1, len(input2) - 1)
        
        return input1[:split1] + input2[split2:]
```

---

## Performance Targets

- **Bit Flip:** < 1ms per mutation
- **Havoc:** < 5ms for 200 iterations
- **Dictionary:** < 1ms per injection
- **Batch Generation:** 1000 mutations/sec

---

Status: Mutation engine specification complete
