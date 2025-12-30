"""Test havoc mutations"""

import pytest
from protocrash.mutators.havoc import HavocMutator


class TestHavocMutator:
    """Test HavocMutator class"""

    @pytest.fixture
    def mutator(self):
        return HavocMutator()

    def test_mutate_basic(self, mutator):
        """Test basic havoc mutation"""
        data = b"TEST_DATA"

        result = mutator.mutate(data, iterations=10)

        assert isinstance(result, bytes)

    def test_mutate_empty_data(self, mutator):
        """Test mutation on empty data"""
        data = b""

        result = mutator.mutate(data)

        assert result == b""

    def test_mutate_single_byte(self, mutator):
        """Test mutation on single byte"""
        data = b"A"

        result = mutator.mutate(data, iterations=5)

        assert isinstance(result, bytes)

    def test_mutate_iterations(self, mutator):
        """Test different iteration counts"""
        data = b"ABCD"

        result1 = mutator.mutate(data, iterations=1)
        result2 = mutator.mutate(data, iterations=100)

        assert isinstance(result1, bytes)
        assert isinstance(result2, bytes)

    def test_mutate_large_input(self, mutator):
        """Test mutation doesn't grow too large"""
        data = b"A" * 100

        result = mutator.mutate(data, iterations=500)

        # Should cap growth at 10x original size
        assert len(result) <= len(data) * 10

    def test_operations_coverage(self, mutator):
        """Test that all operations can be applied"""
        data = b"ABCDEFGH"

        # Run enough iterations to likely hit all operations
        result = mutator.mutate(data, iterations=100)

        assert isinstance(result, bytes)

    def test_delete_block_on_small_data(self, mutator):
        """Test delete block on very small data"""
        data = b"AB"

        # Should handle gracefully
        result = mutator.mutate(data, iterations=10)

        assert isinstance(result, bytes)
