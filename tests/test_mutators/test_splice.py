"""Test splice mutations"""

import pytest
from protocrash.mutators.splice import SpliceMutator


class TestSpliceMutator:
    """Test SpliceMutator class"""

    @pytest.fixture
    def mutator(self):
        return SpliceMutator()

    def test_crossover_basic(self, mutator):
        """Test basic crossover"""
        input1 = b"AAAA"
        input2 = b"BBBB"

        result = mutator.crossover(input1, input2)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_crossover_different_sizes(self, mutator):
        """Test crossover with different sized inputs"""
        input1 = b"SHORT"
        input2 = b"LONGER_INPUT"

        result = mutator.crossover(input1, input2)

        assert isinstance(result, bytes)

    def test_crossover_single_byte(self, mutator):
        """Test crossover with single byte inputs"""
        input1 = b"A"
        input2 = b"B"

        result = mutator.crossover(input1, input2)

        # Single byte inputs should return first input
        assert result == input1

    def test_crossover_empty_first(self, mutator):
        """Test crossover with empty first input"""
        input1 = b""
        input2 = b"BBB"

        result = mutator.crossover(input1, input2)

        assert result == input1

    def test_crossover_empty_second(self, mutator):
        """Test crossover with empty second input"""
        input1 = b"AAA"
        input2 = b""

        result = mutator.crossover(input1, input2)

        assert result == input1

    def test_multi_crossover_single_input(self, mutator):
        """Test multi-crossover with single input"""
        inputs = [b"SINGLE"]

        result = mutator.multi_crossover(inputs, count=3)

        assert result == b"SINGLE"

    def test_multi_crossover_multiple_inputs(self, mutator):
        """Test multi-crossover with multiple inputs"""
        inputs = [b"AAAA", b"BBBB", b"CCCC", b"DDDD"]

        result = mutator.multi_crossover(inputs, count=3)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_multi_crossover_count_exceeds_inputs(self, mutator):
        """Test multi-crossover when count > number of inputs"""
        inputs = [b"AAA", b"BBB"]

        result = mutator.multi_crossover(inputs, count=10)

        # Should use all available inputs
        assert isinstance(result, bytes)

    def test_multi_crossover_empty_list(self, mutator):
        """Test multi-crossover with empty input list"""
        inputs = []

        result = mutator.multi_crossover(inputs)

        assert result == b""

    def test_multi_crossover_two_inputs(self, mutator):
        """Test multi-crossover with exactly 2 inputs"""
        inputs = [b"FIRST", b"SECOND"]

        result = mutator.multi_crossover(inputs, count=2)

        assert isinstance(result, bytes)
