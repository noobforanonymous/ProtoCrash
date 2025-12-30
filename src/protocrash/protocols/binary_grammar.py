"""
Binary Protocol Grammar DSL
Inspired by Construct and Kaitai Struct
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List, Callable
from enum import Enum
import struct

class Endianness(Enum):
    BIG = ">"
    LITTLE = "<"
    NATIVE = "="

@dataclass
class Field:
    """Base class for all field types"""
    name: str

    def parse(self, data: bytes, offset: int, context: Dict[str, Any]) -> tuple[Any, int]:
        """Parse field from data. Returns (value, new_offset)"""
        raise NotImplementedError

    def build(self, value: Any, context: Dict[str, Any]) -> bytes:
        """Build field to bytes"""
        raise NotImplementedError

    def size(self, context: Dict[str, Any]) -> Optional[int]:
        """Return fixed size if known, None if variable"""
        return None

@dataclass
class Int8(Field):
    """Signed 8-bit integer"""
    def parse(self, data: bytes, offset: int, context: Dict[str, Any]) -> tuple[int, int]:
        value = struct.unpack_from('b', data, offset)[0]
        return value, offset + 1

    def build(self, value: int, context: Dict[str, Any]) -> bytes:
        if not isinstance(value, int):
            return b''  # Skip invalid types from mutations
        return struct.pack('b', value)

    def size(self, context: Dict[str, Any]) -> int:
        return 1

@dataclass
class UInt8(Field):
    """Unsigned 8-bit integer"""
    def parse(self, data: bytes, offset: int, context: Dict[str, Any]) -> tuple[int, int]:
        value = struct.unpack_from('B', data, offset)[0]
        return value, offset + 1

    def build(self, value: int, context: Dict[str, Any]) -> bytes:
        if not isinstance(value, int):
            return b''  # Skip invalid types from mutations
        return struct.pack('B', value & 0xFF)  # Mask to valid range

    def size(self, context: Dict[str, Any]) -> int:
        return 1

@dataclass
class Int16(Field):
    """Signed 16-bit integer"""
    endian: Endianness = Endianness.BIG

    def parse(self, data: bytes, offset: int, context: Dict[str, Any]) -> tuple[int, int]:
        fmt = self.endian.value + 'h'
        value = struct.unpack_from(fmt, data, offset)[0]
        return value, offset + 2

    def build(self, value: int, context: Dict[str, Any]) -> bytes:
        if not isinstance(value, int):
            return b''  # Skip invalid types from mutations
        fmt = self.endian.value + 'h'
        return struct.pack(fmt, value)

    def size(self, context: Dict[str, Any]) -> int:
        return 2

@dataclass
class UInt16(Field):
    """Unsigned 16-bit integer"""
    endian: Endianness = Endianness.BIG

    def parse(self, data: bytes, offset: int, context: Dict[str, Any]) -> tuple[int, int]:
        fmt = self.endian.value + 'H'
        value = struct.unpack_from(fmt, data, offset)[0]
        return value, offset + 2

    def build(self, value: int, context: Dict[str, Any]) -> bytes:
        if not isinstance(value, int):
            return b''  # Skip invalid types from mutations
        fmt = self.endian.value + 'H'
        return struct.pack(fmt, value)

    def size(self, context: Dict[str, Any]) -> int:
        return 2

@dataclass
class Int32(Field):
    """Signed 32-bit integer"""
    endian: Endianness = Endianness.BIG

    def parse(self, data: bytes, offset: int, context: Dict[str, Any]) -> tuple[int, int]:
        fmt = self.endian.value + 'i'
        value = struct.unpack_from(fmt, data, offset)[0]
        return value, offset + 4

    def build(self, value: int, context: Dict[str, Any]) -> bytes:
        if not isinstance(value, int):
            return b''  # Skip invalid types from mutations
        fmt = self.endian.value + 'i'
        return struct.pack(fmt, value)

    def size(self, context: Dict[str, Any]) -> int:
        return 4

@dataclass
class UInt32(Field):
    """Unsigned 32-bit integer"""
    endian: Endianness = Endianness.BIG

    def parse(self, data: bytes, offset: int, context: Dict[str, Any]) -> tuple[int, int]:
        fmt = self.endian.value + 'I'
        value = struct.unpack_from(fmt, data, offset)[0]
        return value, offset + 4

    def build(self, value: int, context: Dict[str, Any]) -> bytes:
        if not isinstance(value, int):
            return b''  # Skip invalid types from mutations
        fmt = self.endian.value + 'I'
        return struct.pack(fmt, value)

    def size(self, context: Dict[str, Any]) -> int:
        return 4

@dataclass
class Bytes(Field):
    """Variable or fixed length bytes"""
    length: Optional[int] = None  # Fixed length
    length_field: Optional[str] = None  # Reference to length field

    def parse(self, data: bytes, offset: int, context: Dict[str, Any]) -> tuple[bytes, int]:
        if self.length is not None:
            # Fixed length
            value = data[offset:offset + self.length]
            return value, offset + self.length
        elif self.length_field:
            # Variable length from another field
            length = context[self.length_field]
            value = data[offset:offset + length]
            return value, offset + length
        else:
            # Read to end
            value = data[offset:]
            return value, len(data)

    def build(self, value: bytes, context: Dict[str, Any]) -> bytes:
        return value

    def size(self, context: Dict[str, Any]) -> Optional[int]:
        if self.length is not None:
            return self.length
        elif self.length_field and self.length_field in context:
            return context[self.length_field]
        return None

@dataclass
class String(Field):
    """String field (UTF-8)"""
    length: Optional[int] = None
    length_field: Optional[str] = None

    def parse(self, data: bytes, offset: int, context: Dict[str, Any]) -> tuple[str, int]:
        if self.length is not None:
            length = self.length
        elif self.length_field:
            length = context[self.length_field]
        else:
            # Null-terminated
            end = data.find(b'\x00', offset)
            if end == -1:
                end = len(data)
            length = end - offset

        raw_bytes = data[offset:offset + length]
        value = raw_bytes.decode('utf-8', errors='ignore')
        # Advance by the number of bytes consumed, not string length
        return value, offset + len(raw_bytes)

    def build(self, value: str, context: Dict[str, Any]) -> bytes:
        return value.encode('utf-8')

    def size(self, context: Dict[str, Any]) -> Optional[int]:
        if self.length is not None:
            return self.length
        elif self.length_field and self.length_field in context:
            return context[self.length_field]
        return None

@dataclass
class Const(Field):
    """Constant value (magic bytes)"""
    value: bytes

    def parse(self, data: bytes, offset: int, context: Dict[str, Any]) -> tuple[bytes, int]:
        expected = self.value
        actual = data[offset:offset + len(expected)]
        return actual, offset + len(expected)

    def build(self, value: Any, context: Dict[str, Any]) -> bytes:
        return self.value

    def size(self, context: Dict[str, Any]) -> int:
        return len(self.value)

@dataclass
class Struct(Field):
    """Nested structure"""
    fields: List[Field] = field(default_factory=list)

    def parse(self, data: bytes, offset: int, context: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
        result = {}
        current_offset = offset

        for f in self.fields:
            value, current_offset = f.parse(data, current_offset, {**context, **result})
            result[f.name] = value

        return result, current_offset

    def build(self, value: Dict[str, Any], context: Dict[str, Any]) -> bytes:
        result = b""
        for f in self.fields:
            if f.name in value:
                result += f.build(value[f.name], {**context, **value})
        return result

class Grammar:
    """Binary protocol grammar"""

    def __init__(self, name: str, fields: List[Field]):
        self.name = name
        self.fields = fields

    def parse(self, data: bytes) -> Dict[str, Any]:
        """Parse binary data according to grammar"""
        result = {}
        offset = 0

        for field in self.fields:
            value, offset = field.parse(data, offset, result)
            result[field.name] = value

        return result

    def build(self, values: Dict[str, Any]) -> bytes:
        """Build binary data from values (with auto length fixing)"""
        # First pass: compute sizes
        context = values.copy()

        # Auto-fix length fields
        for field in self.fields:
            if isinstance(field, (UInt8, UInt16, UInt32, Int8, Int16, Int32)):
                # Check if this is a length field
                for other_field in self.fields:
                    if isinstance(other_field, (Bytes, String)):
                        if other_field.length_field == field.name:
                            # Auto-fix length
                            if other_field.name in values:
                                data = values[other_field.name]
                                if isinstance(data, str):
                                    data = data.encode('utf-8')
                                context[field.name] = len(data)

        # Second pass: build
        result = b""
        for field in self.fields:
            # Always build Const fields, otherwise check if in context
            if isinstance(field, Const):
                result += field.build(None, context)
            elif field.name in context:
                result += field.build(context[field.name], context)

        return result
