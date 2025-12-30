"""
Tests for Binary Parser
"""

import pytest
from protocrash.parsers.binary_parser import BinaryParser, BinaryMessage
from protocrash.protocols.binary_grammar import (
    Grammar, UInt8, UInt16, Bytes, Const, Endianness
)

class TestBinaryParser:
    """Test Binary Parser"""
    
    def test_parse_simple_message(self):
        """Test parsing simple binary message"""
        grammar = Grammar("Simple", [
            UInt8("type"),
            UInt8("length"),
            Bytes("data", length_field="length")
        ])
        
        raw = b"\x01\x05Hello"
        msg = BinaryParser.parse(raw, grammar)
        
        assert msg.fields["type"] == 1
        assert msg.fields["length"] == 5
        assert msg.fields["data"] == b"Hello"
        assert msg.raw_data == raw
    
    def test_reconstruct_message(self):
        """Test reconstructing binary message"""
        grammar = Grammar("Simple", [
            UInt16("length", Endianness.BIG),
            Bytes("payload", length_field="length")
        ])
        
        msg = BinaryMessage(
            grammar=grammar,
            fields={"length": 3, "payload": b"ABC"}
        )
        
        data = BinaryParser.reconstruct(msg)
        assert data == b"\x00\x03ABC"
    
    def test_auto_length_fix_on_reconstruct(self):
        """Test automatic length fixing during reconstruction"""
        grammar = Grammar("AutoFix", [
            UInt8("length"),
            Bytes("data", length_field="length")
        ])
        
        # Create message with intentionally wrong length
        msg = BinaryMessage(
            grammar=grammar,
            fields={
                "length": 100,  # Wrong
                "data": b"Test"  # Actual length is 4
            }
        )
        
        data = BinaryParser.reconstruct(msg)
        assert data == b"\x04Test"  # Length auto-fixed to 4
    
    def test_parse_invalid_data(self):
        """Test parsing invalid data"""
        grammar = Grammar("Test", [
            UInt8("field")
        ])
        
        # Empty data
        msg = BinaryParser.parse(b"", grammar)
        assert msg.fields == {}
    
    def test_parse_with_magic(self):
        """Test parsing with magic bytes"""
        grammar = Grammar("WithMagic", [
            Const("magic", b"\xDE\xAD"),
            UInt8("version"),
            UInt8("command")
        ])
        
        raw = b"\xDE\xAD\x01\x02"
        msg = BinaryParser.parse(raw, grammar)
        
        assert msg.fields["magic"] == b"\xDE\xAD"
        assert msg.fields["version"] == 1
        assert msg.fields["command"] == 2
    
    def test_to_bytes_method(self):
        """Test BinaryMessage.to_bytes()"""
        grammar = Grammar("Test", [
            UInt8("a"),
            UInt8("b")
        ])
        
        msg = BinaryMessage(
            grammar=grammar,
            fields={"a": 10, "b": 20}
        )
        
        assert msg.to_bytes() == b"\x0A\x14"
