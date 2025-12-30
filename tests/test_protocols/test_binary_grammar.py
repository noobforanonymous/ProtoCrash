"""
Tests for Binary Grammar DSL
"""

import pytest
from protocrash.protocols.binary_grammar import (
    Grammar, UInt8, UInt16, UInt32, Int8, Int16, Int32,
    Bytes, String, Const, Endianness, Struct
)

class TestBinaryGrammar:
    """Test Binary Grammar DSL"""
    
    def test_uint8_parse_build(self):
        """Test UInt8 field"""
        field = UInt8("test")
        
        # Parse
        value, offset = field.parse(b"\xFF\x00", 0, {})
        assert value == 255
        assert offset == 1
        
        # Build
        data = field.build(128, {})
        assert data == b"\x80"
    
    def test_uint16_big_endian(self):
        """Test UInt16 big endian"""
        field = UInt16("test", Endianness.BIG)
        
        value, offset = field.parse(b"\x01\x02", 0, {})
        assert value == 258  # 0x0102
        
        data = field.build(258, {})
        assert data == b"\x01\x02"
    
    def test_uint16_little_endian(self):
        """Test UInt16 little endian"""
        field = UInt16("test", Endianness.LITTLE)
        
        value, offset = field.parse(b"\x01\x02", 0, {})
        assert value == 513  # 0x0201
        
        data = field.build(513, {})
        assert data == b"\x01\x02"
    
    def test_bytes_fixed_length(self):
        """Test Bytes with fixed length"""
        field = Bytes("data", length=4)
        
        value, offset = field.parse(b"ABCDEF", 0, {})
        assert value == b"ABCD"
        assert offset == 4
        
        data = field.build(b"TEST", {})
        assert data == b"TEST"
    
    def test_bytes_variable_length(self):
        """Test Bytes with length field"""
        field = Bytes("data", length_field="length")
        context = {"length": 3}
        
        value, offset = field.parse(b"ABCDEF", 0, context)
        assert value == b"ABC"
        assert offset == 3
    
    def test_string_parsing(self):
        """Test String field"""
        field = String("name", length=5)
        
        value, offset = field.parse(b"Hello World", 0, {})
        assert value == "Hello"
        assert offset == 5
    
    def test_const_field(self):
        """Test Const (magic bytes)"""
        field = Const("magic", b"\xDE\xAD\xBE\xEF")
        
        value, offset = field.parse(b"\xDE\xAD\xBE\xEF\xFF", 0, {})
        assert value == b"\xDE\xAD\xBE\xEF"
        assert offset == 4
        
        data = field.build(None, {})
        assert data == b"\xDE\xAD\xBE\xEF"
    
    def test_grammar_simple(self):
        """Test simple grammar"""
        grammar = Grammar("Test", [
            UInt8("version"),
            UInt16("length", Endianness.BIG),
            Bytes("data", length_field="length")
        ])
        
        # Parse
        result = grammar.parse(b"\x01\x00\x05Hello")
        assert result["version"] == 1
        assert result["length"] == 5
        assert result["data"] == b"Hello"
        
        # Build
        data = grammar.build(result)
        assert data == b"\x01\x00\x05Hello"
    
    def test_auto_length_fixing(self):
        """Test automatic length field fixing"""
        grammar = Grammar("Test", [
            UInt16("length", Endianness.BIG),
            Bytes("payload", length_field="length")
        ])
        
        # Build with wrong length
        data = grammar.build({
            "length": 999,  # Wrong value
            "payload": b"ABC"  # Actual length is 3
        })
        
        # Should auto-fix to correct length
        assert data == b"\x00\x03ABC"
    
    def test_int8_signed(self):
        """Test signed Int8"""
        field = Int8("test")
        
        value, _ = field.parse(b"\xFF", 0, {})
        assert value == -1
        
        data = field.build(-128, {})
        assert data == b"\x80"
    
    def test_complex_grammar(self):
        """Test complex nested grammar"""
        grammar = Grammar("Complex", [
            Const("magic", b"\xCA\xFE"),
            UInt8("version"),
            UInt16("name_len", Endianness.BIG),
            String("name", length_field="name_len"),
            UInt32("data_len", Endianness.BIG),
            Bytes("data", length_field="data_len")
        ])
        
        # Build
        values = {
            "version": 1,
            "name": "Test",
            "data": b"HelloWorld"
        }
        
        data = grammar.build(values)
        
        # Parse back
        result = grammar.parse(data)
        assert result["version"] == 1
        assert result["name"] == "Test"
        assert result["data"] == b"HelloWorld"
    
    def test_int16_signed(self):
        """Test signed Int16"""
        field = Int16("test", Endianness.BIG)
        
        value, _ = field.parse(b"\xFF\xFF", 0, {})
        assert value == -1
        
        data = field.build(-1, {})
        assert data == b"\xFF\xFF"
    
    def test_int32_signed(self):
        """Test signed Int32"""
        field = Int32("test", Endianness.LITTLE)
        
        value, _ = field.parse(b"\xFF\xFF\xFF\xFF", 0, {})
        assert value == -1
        
        data = field.build(-2147483648, {})
        assert len(data) == 4
    
    def test_uint32_parse_build(self):
        """Test UInt32"""
        field = UInt32("test", Endianness.BIG)
        
        value, _ = field.parse(b"\x00\x00\x00\xFF", 0, {})
        assert value == 255
        
        data = field.build(4294967295, {})
        assert data == b"\xFF\xFF\xFF\xFF"
    
    def test_bytes_to_end(self):
        """Test Bytes reading to end of data"""
        field = Bytes("data")  # No length specified
        
        value, offset = field.parse(b"HelloWorld", 0, {})
        assert value == b"HelloWorld"
        assert offset == 10
    
    def test_string_null_terminated(self):
        """Test null-terminated string"""
        field = String("name")  # No length
        
        value, offset = field.parse(b"Hello\x00World", 0, {})
        assert value == "Hello"
        assert offset == 5
    
    def test_string_variable_length(self):
        """Test String with length_field"""
        field = String("name", length_field="name_len")
        context = {"name_len": 3}
        
        value, offset = field.parse(b"HelloWorld", 0, context)
        assert value == "Hel"
        assert offset == 3
    
    def test_string_size_methods(self):
        """Test String.size()"""
        field1 = String("test", length=10)
        assert field1.size({}) == 10
        
        field2 = String("test", length_field="len")
        assert field2.size({"len": 5}) == 5
        
        field3 = String("test")  # Variable
        assert field3.size({}) is None
    
    def test_bytes_size_methods(self):
        """Test Bytes.size()"""
        field1 = Bytes("data", length=20)
        assert field1.size({}) == 20
        
        field2 = Bytes("data", length_field="size")
        assert field2.size({"size": 100}) == 100
        
        field3 = Bytes("data")
        assert field3.size({}) is None
    
    def test_struct_nested(self):
        """Test nested Struct field"""
        inner = Struct("inner", [
            UInt8("a"),
            UInt8("b")
        ])
        
        value, offset = inner.parse(b"\x01\x02\x03", 0, {})
        assert value == {"a": 1, "b": 2}
        assert offset == 2
        
        data = inner.build({"a": 10, "b": 20}, {})
        assert data == b"\x0A\x14"
    
    def test_field_size_methods(self):
        """Test size() methods for all field types"""
        assert UInt8("f").size({}) == 1
        assert UInt16("f").size({}) == 2
        assert UInt32("f").size({}) == 4
        assert Int8("f").size({}) == 1
        assert Int16("f").size({}) == 2
        assert Int32("f").size({}) == 4
        assert Const("f", b"test").size({}) == 4
