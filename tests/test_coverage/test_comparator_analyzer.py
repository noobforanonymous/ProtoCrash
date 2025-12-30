"""Test coverage comparator and analyzer"""

import pytest
from protocrash.monitors.coverage_comparator import CoverageComparator
from protocrash.monitors.coverage_analyzer import CoverageAnalyzer, CoverageStats


class TestCoverageComparator:
    """Test CoverageComparator class"""

    @pytest.fixture
    def comparator(self):
        return CoverageComparator()

    def test_has_new_bits_with_new_coverage(self, comparator):
        """Test detecting new coverage bits"""
        virgin_map = bytearray([0xFF] * 100)
        trace_bits = bytearray([0x00] * 100)
        trace_bits[50] = 0x01  # New bit
        
        result = comparator.has_new_bits(virgin_map, trace_bits)
        
        assert result is True

    def test_has_new_bits_no_new_coverage(self, comparator):
        """Test no new coverage"""
        virgin_map = bytearray([0x00] * 100)
        trace_bits = bytearray([0x01] * 100)
        
        result = comparator.has_new_bits(virgin_map, trace_bits)
        
        assert result is False

    def test_has_new_bits_different_sizes(self, comparator):
        """Test with different sized bitmaps"""
        virgin_map = bytearray([0xFF] * 100)
        trace_bits = bytearray([0x01] * 50)
        
        result = comparator.has_new_bits(virgin_map, trace_bits)
        
        assert result is False

    def test_count_new_bits(self, comparator):
        """Test counting new bits"""
        virgin_map = bytearray([0xFF] * 100)
        trace_bits = bytearray([0x00] * 100)
        trace_bits[10] = 0x01  # 1 bit
        trace_bits[20] = 0x03  # 2 bits
        
        count = comparator.count_new_bits(virgin_map, trace_bits)
        
        assert count == 3

    def test_count_new_bits_no_new(self, comparator):
        """Test counting when no new bits"""
        virgin_map = bytearray([0x00] * 100)
        trace_bits = bytearray([0x01] * 100)
        
        count = comparator.count_new_bits(virgin_map, trace_bits)
        
        assert count == 0

    def test_compare_bitmaps_identical(self, comparator):
        """Test comparing identical bitmaps"""
        bitmap1 = bytearray([0xAB] * 100)
        bitmap2 = bytearray([0xAB] * 100)
        
        similarity = comparator.compare_bitmaps(bitmap1, bitmap2)
        
        assert similarity == 1.0

    def test_compare_bitmaps_different(self, comparator):
        """Test comparing different bitmaps"""
        bitmap1 = bytearray([0xAB] * 100)
        bitmap2 = bytearray([0xCD] * 100)
        
        similarity = comparator.compare_bitmaps(bitmap1, bitmap2)
        
        assert similarity == 0.0

    def test_compare_bitmaps_partial(self, comparator):
        """Test comparing partially similar bitmaps"""
        bitmap1 = bytearray([0xAB] * 100)
        bitmap2 = bytearray([0xAB] * 50 + [0xCD] * 50)
        
        similarity = comparator.compare_bitmaps(bitmap1, bitmap2)
        
        assert similarity == 0.5

    def test_compare_bitmaps_different_sizes(self, comparator):
        """Test comparing different sized bitmaps"""
        bitmap1 = bytearray([0xAB] * 100)
        bitmap2 = bytearray([0xAB] * 50)
        
        similarity = comparator.compare_bitmaps(bitmap1, bitmap2)
        
        assert similarity == 0.0


class TestCoverageAnalyzer:
    """Test CoverageAnalyzer class"""

    @pytest.fixture
    def analyzer(self):
        return CoverageAnalyzer()

    def test_analyze_empty_bitmap(self, analyzer):
        """Test analyzing empty bitmap"""
        bitmap = bytearray([0] * 100)
        
        stats = analyzer.analyze(bitmap)
        
        assert stats.total_edges == 0
        assert stats.unique_edges == 0
        assert stats.edge_density == 0.0

    def test_analyze_with_coverage(self, analyzer):
        """Test analyzing bitmap with coverage"""
        bitmap = bytearray([0] * 100)
        bitmap[10] = 5
        bitmap[20] = 10
        bitmap[30] = 150
        
        stats = analyzer.analyze(bitmap)
        
        assert stats.unique_edges == 3
        assert stats.total_edges == 5 + 10 + 150
        assert stats.max_hit_count == 150
        assert stats.edge_density > 0

    def test_analyze_hot_edges(self, analyzer):
        """Test identifying hot edges"""
        bitmap = bytearray([0] * 1000)
        bitmap[100] = 200  # Hot edge
        bitmap[200] = 150  # Hot edge
        bitmap[300] = 50   # Not hot
        
        stats = analyzer.analyze(bitmap)
        
        assert len(stats.hot_edges) == 2
        assert 100 in stats.hot_edges
        assert 200 in stats.hot_edges

    def test_identify_interesting_inputs_empty(self, analyzer):
        """Test with empty corpus"""
        corpus_coverage = {}
        
        interesting = analyzer.identify_interesting_inputs(corpus_coverage)
        
        assert interesting == []

    def test_identify_interesting_inputs_single(self, analyzer):
        """Test with single input"""
        bitmap = bytearray([0] * 100)
        bitmap[10] = 5
        
        corpus_coverage = {"input1": bitmap}
        
        interesting = analyzer.identify_interesting_inputs(corpus_coverage, map_size=100)
        
        assert interesting == ["input1"]

    def test_identify_interesting_inputs_multiple(self, analyzer):
        """Test with multiple inputs"""
        bitmap1 = bytearray([0] * 100)
        bitmap1[10] = 5
        
        bitmap2 = bytearray([0] * 100)
        bitmap2[20] = 3  # New coverage
        
        bitmap3 = bytearray([0] * 100)
        bitmap3[10] = 5  # Duplicate of bitmap1
        
        corpus_coverage = {
            "input1": bitmap1,
            "input2": bitmap2,
            "input3": bitmap3
        }
        
        interesting = analyzer.identify_interesting_inputs(corpus_coverage, map_size=100)
        
        # input1 and input2 are interesting, input3 is duplicate
        assert len(interesting) == 2
        assert "input1" in interesting
        assert "input2" in interesting
