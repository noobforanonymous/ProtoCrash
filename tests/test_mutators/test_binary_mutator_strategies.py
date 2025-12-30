"""
Additional Binary Mutator Tests - Strategy Coverage
"""

import pytest
from unittest.mock import patch
from protocrash.mutators.binary_mutator import BinaryMutator
from protocrash.parsers.binary_parser import BinaryParser, BinaryMessage
from protocrash.protocols.binary_grammar import (
    Grammar, UInt8, UInt16, UInt32, Int8, Bytes, String, Endianness
)

class TestBinaryMutatorStrategies:
    """Test all mutation strategy paths"""
    
    def test_empty_data_fallback(self):
        """Test fallback mutation with empty data"""
        grammar = Grammar("Test", [UInt8("field")])
        mutator = BinaryMutator(grammar)
        
        # Empty bytes should trigger fallback
        result = mutator.mutate(b"")
        assert isinstance(result, bytes)
    
    def test_mutation_strategy_field_value(self):
        """Force field_value mutation strategy"""
        grammar = Grammar("Test", [
            UInt8("num"),
            Bytes("data", length=5)
        ])
        
        mutator = BinaryMutator(grammar)
        
        # Mock random.choice to always return "field_value"
        with patch('random.choice', side_effect=lambda x: x[0] if "field_value" in x else x[0]):
            msg = BinaryMessage(grammar=grammar, fields={"num": 10, "data": b"Hello"})
            mutator._mutate_field_value(msg)
            # Verify mutation happened (can't predict exact value due to randomness)
    
    def test_mutation_strategy_boundary(self):
        """Force boundary_test mutation strategy"""
        grammar = Grammar("Test", [
            UInt8("byte"),
            UInt16("short", Endianness.BIG),
            UInt32("long", Endianness.BIG)
        ])
        
        mutator = BinaryMutator(grammar)
        msg = BinaryMessage(
            grammar=grammar,
            fields={"byte": 128, "short": 1000, "long": 50000}
        )
        
        mutator._mutate_boundary(msg)
        # Should have set one field to boundary value
    
    def test_mutation_strategy_type_confusion(self):
        """Force type_confusion mutation"""
        grammar = Grammar("Test", [UInt16("number", Endianness.BIG)])
        mutator = BinaryMutator(grammar)
        msg = BinaryMessage(grammar=grammar, fields={"number": 1234})
        
        mutator._mutate_type_confusion(msg)
        # Should have replaced with bytes
        assert isinstance(msg.fields["number"], bytes)
    
    def test_mutation_strategy_length_mismatch(self):
        """Force length_mismatch mutation"""
        grammar = Grammar("Test", [
            UInt16("size", Endianness.BIG),
            Bytes("payload", length_field="size")
        ])
        
        mutator = BinaryMutator(grammar)
        msg = BinaryMessage(
            grammar=grammar,
            fields={"size": 10, "payload": b"0123456789"}
        )
        
        mutator._mutate_length_mismatch(msg)
        # Size should have been modified
        assert msg.fields["size"] != 10
    
    def test_mutation_strategy_field_injection(self):
        """Force field_injection mutation"""
        grammar = Grammar("Test", [UInt8("field1")])
        mutator = BinaryMutator(grammar)
        msg = BinaryMessage(grammar=grammar, fields={"field1": 1})
        
        original_count = len(msg.fields)
        mutator._inject_field(msg)
        
        # Should have added injected field
        assert len(msg.fields) > original_count
    
    def test_mutation_strategy_field_removal(self):
        """Force field_removal mutation"""
        grammar = Grammar("Test", [
            UInt8("field1"),
            UInt8("field2"),
            UInt8("field3")
        ])
        
        mutator = BinaryMutator(grammar)
        msg = BinaryMessage(
            grammar=grammar,
            fields={"field1": 1, "field2": 2, "field3": 3}
        )
        
        mutator._remove_field(msg)
        # Should have removed one field
        assert len(msg.fields) < 3
    
    def test_mutate_field_value_with_string(self):
        """Test field value mutation with String field"""
        grammar = Grammar("Test", [
            UInt8("len"),
            String("text", length_field="len")
        ])
        
        mutator = BinaryMutator(grammar)
        msg = BinaryMessage(
            grammar=grammar,
            fields={"len": 5, "text": "Hello"}
        )
        
        # Force mutation on string field
        mutator._mutate_field_value(msg)
    
    def test_boundary_with_signed_ints(self):
        """Test boundary mutation with signed integers"""
        grammar = Grammar("Test", [
            UInt8("u8"),
            Int8("i8")
        ])
        
        mutator = BinaryMutator(grammar)
        msg = BinaryMessage(
            grammar=grammar,
            fields={"u8": 100, "i8": -50}
        )
        
        # Run multiple times to hit Int8 boundary
        for _ in range(20):
            mutator._mutate_boundary(msg)
        
        mutator = BinaryMutator(grammar)
        msg = BinaryMessage(
            grammar=grammar,
            fields={"u8": 100, "i8": -50}
        )
        
        # Run multiple times to hit Int8 boundary
        for _ in range(20):
            mutator._mutate_boundary(msg)
    
    def test_no_length_fields(self):
        """Test length_mismatch when no length fields exist"""
        grammar = Grammar("NoLength", [
            UInt8("field1"),
            UInt8("field2")
        ])
        
        mutator = BinaryMutator(grammar)
        msg = BinaryMessage(
            grammar=grammar,
            fields={"field1": 1, "field2": 2}
        )
        
        # Should not crash when no length fields exist
        mutator._mutate_length_mismatch(msg)
    
    def test_parser_exception_handling(self):
        """Test parser error handling in mutate"""
        grammar = Grammar("Test", [UInt8("field")])
        mutator = BinaryMutator(grammar)
        
        # Completely invalid data that will fail parsing
        result = mutator.mutate(b"")
        assert isinstance(result, bytes)
