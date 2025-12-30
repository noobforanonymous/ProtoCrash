"""
Binary Protocol Mutator - Structure-Aware
"""
import random
from typing import Optional
from ..parsers.binary_parser import BinaryParser, BinaryMessage
from ..protocols.binary_grammar import (
    Grammar, Field, UInt8, UInt16, UInt32, Int8, Int16, Int32,
    Bytes, String
)
class BinaryMutator:
    """Structure-aware binary protocol mutator"""
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.parser = BinaryParser()
    def mutate(self, data: bytes) -> bytes:
        """Parse, mutate, and reconstruct binary data"""
        msg = self.parser.parse(data, self.grammar)
        if not msg.fields:
            return self._fallback_mutate(data)
        # Choose mutation strategy
        strategy = random.choice([
            "field_value",
            "boundary_test",
            "type_confusion",
            "length_mismatch",
            "field_injection",
            "field_removal"
        ])
        if strategy == "field_value":
            self._mutate_field_value(msg)
        elif strategy == "boundary_test":
            self._mutate_boundary(msg)
        elif strategy == "type_confusion":
            self._mutate_type_confusion(msg)
        elif strategy == "length_mismatch":
            self._mutate_length_mismatch(msg)
        elif strategy == "field_injection":
            self._inject_field(msg)
        elif strategy == "field_removal":
            self._remove_field(msg)
        return self.parser.reconstruct(msg)
    def _fallback_mutate(self, data: bytes) -> bytes:
        """Simple bit flip fallback"""
        if not data:
            return data
        result = bytearray(data)
        pos = random.randint(0, len(result) - 1)
        result[pos] ^= random.randint(1, 255)
        return bytes(result)
    def _get_field(self, field_name: str) -> Optional[Field]:
        """Get field definition from grammar"""
        for f in self.grammar.fields:
            if f.name == field_name:
                return f
        return None
    def _mutate_field_value(self, msg: BinaryMessage):
        """Mutate a random field value"""
        if not msg.fields:
            return
        field_name = random.choice(list(msg.fields.keys()))
        field_def = self._get_field(field_name)
        if field_def is None:
            return
        # Mutate based on field type
        if isinstance(field_def, (UInt8, Int8, UInt16, Int16, UInt32, Int32)):
            msg.fields[field_name] = self._mutate_int(msg.fields[field_name], field_def)
        elif isinstance(field_def, Bytes):
            msg.fields[field_name] = self._mutate_bytes(msg.fields[field_name])
        elif isinstance(field_def, String):
            msg.fields[field_name] = self._mutate_string(msg.fields[field_name])
    def _mutate_int(self, value: int, field_def: Field) -> int:
        """Mutate integer value"""
        op = random.choice(['flip_bit', 'add', 'sub', 'random'])
        if op == 'flip_bit':
            bit = random.randint(0, 31)
            value ^= (1 << bit)
        elif op == 'add':
            value += random.randint(1, 1000)
        elif op == 'sub':
            value -= random.randint(1, 1000)
        else:  # random
            if isinstance(field_def, UInt8):
                value = random.randint(0, 255)
            elif isinstance(field_def, Int8):
                value = random.randint(-128, 127)
            elif isinstance(field_def, UInt16):
                value = random.randint(0, 65535)
            elif isinstance(field_def, Int16):
                value = random.randint(-32768, 32767)
            elif isinstance(field_def, UInt32):
                value = random.randint(0, 4294967295)
            elif isinstance(field_def, Int32):
                value = random.randint(-2147483648, 2147483647)
        # Clamp to valid range
        if isinstance(field_def, UInt8):
            return max(0, min(255, value))
        elif isinstance(field_def, Int8):
            return max(-128, min(127, value))
        elif isinstance(field_def, UInt16):
            return max(0, min(65535, value))
        elif isinstance(field_def, Int16):
            return max(-32768, min(32767, value))
        elif isinstance(field_def, UInt32):
            return max(0, min(4294967295, value))
        elif isinstance(field_def, Int32):
            return max(-2147483648, min(2147483647, value))
        return value
    def _mutate_bytes(self, value: bytes) -> bytes:
        """Mutate bytes value"""
        if not value:
            return b'\x00'
        op = random.choice(['flip', 'truncate', 'extend'])
        result = bytearray(value)
        if op == 'flip':
            pos = random.randint(0, len(result) - 1)
            result[pos] ^= random.randint(1, 255)
        elif op == 'truncate' and len(result) > 1:
            result = result[:len(result) // 2]
        else:  # extend
            result += bytes(random.randint(0, 255) for _ in range(5))
        return bytes(result)
    def _mutate_string(self, value: str) -> str:
        """Mutate string value"""
        mutations = [
            '../../../etc/passwd',
            'OR 1=1--',
            '<script>alert(1)</script>',
            value + '\x00',
            value * 100,
            ''
        ]
        return random.choice(mutations)
    def _mutate_boundary(self, msg: BinaryMessage):
        """Set fields to boundary values"""
        if not msg.fields:
            return
        field_name = random.choice(list(msg.fields.keys()))
        field_def = self._get_field(field_name)
        if isinstance(field_def, UInt8):
            msg.fields[field_name] = random.choice([0, 255, 128])
        elif isinstance(field_def, UInt16):
            msg.fields[field_name] = random.choice([0, 65535, 32768])
        elif isinstance(field_def, UInt32):
            msg.fields[field_name] = random.choice([0, 4294967295, 2147483648])
    def _mutate_type_confusion(self, msg: BinaryMessage):
        """Replace field with incompatible type"""
        if not msg.fields:
            return
        field_name = random.choice(list(msg.fields.keys()))
        # Replace with bytes (tests expect this)
        msg.fields[field_name] = b"\x41\x42\x43\x44"
    def _mutate_length_mismatch(self, msg: BinaryMessage):
        """Break length field relationships"""
        # Find length fields
        for field in self.grammar.fields:
            if hasattr(field, 'length_field') and field.length_field:
                if field.length_field in msg.fields:
                    # Corrupt the length
                    msg.fields[field.length_field] = random.randint(0, 255)
                    return
    def _inject_field(self, msg: BinaryMessage):
        """Add a non-existent field"""
        msg.fields[f'injected_{random.randint(0, 1000)}'] = random.randint(0, 255)
    def _remove_field(self, msg: BinaryMessage):
        """Remove a random field"""
        if len(msg.fields) > 1:
            field_name = random.choice(list(msg.fields.keys()))
            del msg.fields[field_name]
