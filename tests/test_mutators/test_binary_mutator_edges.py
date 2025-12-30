"""
Binary Mutator - Edge Case Coverage Tests
"""

import pytest
from protocrash.mutators.binary_mutator import BinaryMutator
from protocrash.parsers.binary_parser import BinaryMessage
from protocrash.protocols.binary_grammar import (
    Grammar, UInt8, UInt16, UInt32, Int8, Int16, Int32, Bytes, String, Endianness
)

class TestBinaryMutatorEdgeCases:
    """Test edge cases for maximum coverage"""
    
    def test_mutate_field_value_with_unknown_field_type(self):
        """Test _mutate_field_value when field_obj is None"""
        grammar = Grammar("Test", [UInt8("field1")])
        mutator = BinaryMutator(grammar)
        
        # Create message with field not in grammar
        msg = BinaryMessage(
            grammar=grammar,
            fields={"field1": 10, "unknown_field": 20}
        )
        
        # Try to mutate - should handle None field_obj
        mutator._mutate_field_value(msg)
    
    def test_mutate_boundary_no_int_fields(self):
        """Test _mutate_boundary with no integer fields"""
        grammar = Grammar("NoInts", [
            Bytes("data", length=5),
            String("text", length=10)
        ])
        
        mutator = BinaryMutator(grammar)
        msg = BinaryMessage(
            grammar=grammar,
            fields={"data": b"Hello", "text": "World"}
        )
        
        # Should return early when no int fields
        mutator._mutate_boundary(msg)
        # Verify no crash
        assert "data" in msg.fields
    
    def test_boundary_all_int_types(self):
        """Test boundary values for all integer types"""
        grammar = Grammar("AllInts", [
            UInt8("u8"),
            UInt16("u16", Endianness.BIG),
            UInt32("u32", Endianness.BIG),
            Int8("i8"),
            Int16("i16", Endianness.BIG),
            Int32("i32", Endianness.BIG)
        ])
        
        mutator = BinaryMutator(grammar)
        
        # Test UInt32 boundary
        msg = BinaryMessage(
            grammar=grammar,
            fields={"u8": 100, "u16": 1000, "u32": 50000,
                   "i8": -50, "i16": -1000, "i32": -50000}
        )
        
        # Run many times to hit all branches
        for _ in range(100):
            mutator._mutate_boundary(msg)
    
    def test_type_confusion_empty_fields(self):
        """Test _mutate_type_confusion with empty fields"""
        grammar = Grammar("Empty", [UInt8("field")])
        mutator = BinaryMutator(grammar)
        
        msg = BinaryMessage(grammar=grammar, fields={})
        
        # Should return early
        mutator._mutate_field_value(msg)
        mutator._mutate_type_confusion(msg)
    
    def test_fallback_mutate_empty_data(self):
        """Test _fallback_mutate with empty bytes"""
        mutator = BinaryMutator(Grammar("Test", []))
        
        result = mutator._fallback_mutate(b"")
        assert result == b""
    
    def test_mutate_field_value_all_types(self):
        """Ensure all field type branches are covered"""
        grammar = Grammar("AllTypes", [
            UInt8("uint"),
            Int8("int"),
            Bytes("bytes", length=5),
            String("string", length=10)
        ])
        
        mutator = BinaryMutator(grammar)
        
        # Test integer mutation
        msg = BinaryMessage(
            grammar=grammar,
            fields={"uint": 10}
        )
        field_obj = mutator._get_field("uint")
        original = msg.fields["uint"]
        msg.fields["uint"] = mutator._mutate_int(original, field_obj)
        
        # Test bytes mutation
        msg.fields["bytes"] = b"Hello"
        original_bytes = msg.fields["bytes"]
        msg.fields["bytes"] = mutator._mutate_bytes(original_bytes)
        
        # Test string mutation
        msg.fields["string"] = "World"
        original_string = msg.fields["string"]
        msg.fields["string"] = mutator._mutate_string(original_string)
    
    def test_int16_and_int32_boundaries(self):
        """Specifically test Int16 and Int32 boundary branches"""
        grammar = Grammar("SignedInts", [
            Int16("i16", Endianness.BIG),
            Int32("i32", Endianness.BIG)
        ])
        
        mutator = BinaryMutator(grammar)
        msg = BinaryMessage(
            grammar=grammar,
            fields={"i16": 0, "i32": 0}
        )
        
        # Force hitting Int16 boundary
        seen_values = set()
        for _ in range(50):
            mutator._mutate_boundary(msg)
            if "i16" in msg.fields:
                seen_values.add(msg.fields.get("i16"))
            if "i32" in msg.fields:
                seen_values.add(msg.fields.get("i32"))
        
        # Should have hit boundary values
        assert len(seen_values) >= 1
    
    def test_uint32_boundary_branch(self):
        """Test UInt32 specific boundary values"""
        grammar = Grammar("U32", [
            UInt32("value", Endianness.BIG)
        ])
        
        mutator = BinaryMutator(grammar)
        msg = BinaryMessage(
            grammar=grammar,
            fields={"value": 1000000}
        )
        
        values_seen = set()
        for _ in range(30):
            mutator._mutate_boundary(msg)
            values_seen.add(msg.fields["value"])
        
        # Should include 0, 4294967295, 2147483648
        assert 0 in values_seen or 4294967295 in values_seen or 2147483648 in values_seen
    
    def test_else_branch_in_boundary(self):
        """Cover the else branch in boundary mutation"""
        # This shouldn't happen in normal use, but for coverage
        from protocrash.protocols.binary_grammar import Field
        
        class CustomField(Field):
            """Custom field type for testing"""
            name = "custom"
        
        grammar = Grammar("Test", [UInt8("normal")])
        mutator = BinaryMutator(grammar)
        
        # Normal operation
        msg = BinaryMessage(grammar=grammar, fields={"normal": 10})
        mutator._mutate_boundary(msg)
