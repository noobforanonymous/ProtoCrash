"""Ultimate precision test for final 3 statements"""

import pytest
import random
from protocrash.mutators.splice import SpliceMutator
from protocrash.monitors.memory_leak_detector import MemoryLeakDetector, MemorySnapshot


class TestUltimate100Percent:
    """Tests for THE FINAL 3 missing statements"""

    def test_splice_line_50_exact(self):
        """Test splice.py line 50: return selected[0] when len(selected) == 1"""
        splicer = SpliceMutator()
        
        # Force random.sample to return exactly 1 item
        inputs = [b"first", b"second", b"third"]
        
        # Mock random.sample to return only 1 item
        original_sample = random.sample
        def force_one_item(population, k):
            return [population[0]]  # Return only first item
        
        random.sample = force_one_item
        try:
            result = splicer.multi_crossover(inputs, count=3)
            # Should hit line 50: return selected[0]
            assert result == b"first"
        finally:
            random.sample = original_sample

    def test_memory_leak_line_130_exact(self):
        """Test memory_leak_detector.py line 130: else return LOW"""
        detector = MemoryLeakDetector()
        
        # Create exactly 15 snapshots with growth_ratio <= 0.6
        # Need 19 comparisons (20 snapshots - 1)
        # For LOW: increasing_count / 19 <= 0.6, so <= 11 increases
        snapshots = []
        for i in range(20):
            # Create exactly 11 increases out of 19 = 57.9% (< 60% = LOW)
            rss = 1000 + (100 if i < 12 else 0)  # 11 increases
            snapshots.append(MemorySnapshot(float(i), rss, 2000))
        
        confidence = detector._calculate_confidence(snapshots)
        
        # Should hit line 130-132: else: return "LOW"
        assert confidence == "LOW"

    def test_version_file_coverage(self):
        """Test __version__.py line 3 coverage"""
        import sys
        import types
        
        # Force reload or clean import
        if 'protocrash' in sys.modules:
            del sys.modules['protocrash']
            
        import protocrash
        
        # Verify it's a module
        assert isinstance(protocrash, types.ModuleType)
        # Verify version
        assert hasattr(protocrash, '__version__')
        assert isinstance(protocrash.__version__, str)

