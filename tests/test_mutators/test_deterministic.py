"""Test deterministic mutations"""

import pytest
from protocrash.mutators.deterministic import DeterministicMutator


class TestDeterministicMutator:
    """Test DeterministicMutator class"""

    @pytest.fixture
    def mutator(self):
        return DeterministicMutator()

    @pytest.fixture
    def sample_data(self):
        return b"ABCD"

    def test_bit_flips_single(self, mutator, sample_data):
        """Test single bit flip mutations"""
        mutations = mutator.bit_flips(sample_data, flip_counts=[1])

        assert len(mutations) == len(sample_data) * 8
        assert all(len(m) == len(sample_data) for m in mutations)
        assert sample_data not in mutations  # All should be different

    def test_bit_flips_multiple(self, mutator, sample_data):
        """Test multiple bit flip mutations"""
        mutations = mutator.bit_flips(sample_data, flip_counts=[1, 2])

        # Should have mutations for each position
        assert len(mutations) > 0
        assert all(isinstance(m, bytes) for m in mutations)

    def test_byte_flips_single(self, mutator, sample_data):
        """Test single byte flip"""
        mutations = mutator.byte_flips(sample_data, flip_sizes=[1])

        assert len(mutations) == len(sample_data)
        # First mutation should flip first byte
        assert mutations[0] == b"\xbeBCD"  # 'A' (0x41) XOR 0xFF = 0xBE

    def test_byte_flips_multiple(self, mutator, sample_data):
        """Test multiple byte flips"""
        mutations = mutator.byte_flips(sample_data, flip_sizes=[2])

        assert len(mutations) == len(sample_data) - 1
        assert mutations[0] == b"\xbe\xbdCD"  # First 2 bytes flipped

    def test_arithmetic_add(self, mutator):
        """Test arithmetic addition"""
        data = b"\x00\x00\x00\x00"
        mutations = mutator.arithmetic(data, deltas=[1], sizes=[1])

        assert len(mutations) == 4
        assert mutations[0] == b"\x01\x00\x00\x00"
        assert mutations[1] == b"\x00\x01\x00\x00"

    def test_arithmetic_subtract(self, mutator):
        """Test arithmetic subtraction"""
        data = b"\x05\x05\x05\x05"
        mutations = mutator.arithmetic(data, deltas=[-1], sizes=[1])

        assert mutations[0] == b"\x04\x05\x05\x05"

    def test_arithmetic_wraparound(self, mutator):
        """Test arithmetic wrap-around"""
        data = b"\xFF"
        mutations = mutator.arithmetic(data, deltas=[1], sizes=[1])

        assert mutations[0] == b"\x00"  # 0xFF + 1 wraps to 0x00

    def test_interesting_values_8bit(self, mutator):
        """Test 8-bit interesting values"""
        data = b"\x00\x00"
        mutations = mutator.interesting_values(data)

        # Should have mutations for interesting 8-bit values at each position
        assert len(mutations) > 0
        # Check for specific interesting values
        assert b"\x7F\x00" in mutations  # 127 at pos 0
        assert b"\x00\x7F" in mutations  # 127 at pos 1

    def test_interesting_values_16bit(self, mutator):
        """Test 16-bit interesting values"""
        data = b"\x00\x00"
        mutations = mutator.interesting_values(data)

        # Should include 16-bit values
        assert b"\xFF\x00" in mutations  # 255 (16-bit)

    def test_empty_data(self, mutator):
        """Test mutations on empty data"""
        data = b""
        
        assert mutator.bit_flips(data) == []
        assert mutator.byte_flips(data) == []
        assert mutator.arithmetic(data) == []
        assert mutator.interesting_values(data) == []
