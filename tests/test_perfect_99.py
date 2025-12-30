"""PERFECT tests for final 2 lines based on deep research"""

import pytest
from unittest.mock import patch
from protocrash.mutators.splice import SpliceMutator
from protocrash.monitors.memory_leak_detector import MemoryLeakDetector, MemorySnapshot


class TestPerfect99Coverage:
    """Research-based perfect tests for final 2 lines"""

    def test_splice_line_50_with_proper_mocking(self):
        """
        Test splice.py line 50: return selected[0] when len(selected) == 1
        
        Research shows: Use unittest.mock.patch to control random.sample
        to return exactly 1 element, triggering line 50.
        """
        splicer = SpliceMutator()
        inputs = [b"first", b"second", b"third"]
        
        # Patch random.sample to return a list with ONE element
        with patch('random.sample', return_value=[b"single"]):
            result = splicer.multi_crossover(inputs, count=3)
            
            # Should hit line 50: return selected[0]
            assert result == b"single"

    def test_memory_leak_line_130_medium_confidence(self):
        """
        Test memory_leak_detector.py line 130: return "MEDIUM"
        
        Research shows: MEDIUM confidence requires growth_ratio > 0.6 AND <= 0.8
        Formula: increasing_count / (len(snapshots) - 1)
        
        For 20 snapshots (19 comparisons):
        - Need 13-15 increases = 68.4% - 78.9%
        - This falls in MEDIUM range (> 0.6, <= 0.8)
        """
        detector = MemoryLeakDetector()
        
        # Create 20 snapshots with exactly 14 increases out of 19 comparisons
        # Growth ratio = 14/19 = 73.68% (MEDIUM: 0.6 < 0.7368 <= 0.8)
        snapshots = []
        for i in range(20):
            # First 15 always increase (14 increases from 0->14)
            # Then 5 stay same or decrease (0 more increases)
            if i < 15:
                rss = 1000 + (i * 100)  # Always increasing
            else:
                rss = 1000 + (14 * 100)  # Same as last one
            
            snapshots.append(MemorySnapshot(float(i), rss, 2000))
        
        confidence = detector._calculate_confidence(snapshots)
        
        # Should hit line 130: return "MEDIUM"
        assert confidence == "MEDIUM"

    def test_memory_leak_line_130_exact_boundary(self):
        """
        Test memory_leak line 130 with exact 0.6 < ratio <= 0.8 boundary
        
        Using 25 snapshots (24 comparisons):
        - 16 increases = 66.67% (MEDIUM)
        - 19 increases = 79.17% (MEDIUM)
        """
        detector = MemoryLeakDetector()
        
        # Create 25 snapshots with 16 increases = 66.67% growth ratio
        snapshots = []
        for i in range(25):
            # First 17 increase (16 increases), rest same
            rss = 1000 + (i * 100) if i < 17 else 1000 + (16 * 100)
            snapshots.append(MemorySnapshot(float(i), rss, 2000))
        
        confidence = detector._calculate_confidence(snapshots)
        
        # With 66.67% growth (0.6 < 0.6667 <= 0.8), should be MEDIUM
        assert confidence == "MEDIUM"
