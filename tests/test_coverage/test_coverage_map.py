"""Test coverage map"""

import pytest
from protocrash.monitors.coverage_map import CoverageMap


class TestCoverageMap:
    """Test CoverageMap class"""

    @pytest.fixture
    def coverage_map(self):
        return CoverageMap()

    def test_init(self, coverage_map):
        """Test initialization"""
        assert coverage_map.MAP_SIZE == 65536
        assert len(coverage_map.bitmap) == 65536
        assert len(coverage_map.virgin_map) == 65536
        assert coverage_map.prev_location == 0
        assert coverage_map.total_edges_found == 0

    def test_reset(self, coverage_map):
        """Test reset clears bitmap"""
        # Add some coverage
        coverage_map.record_edge(0x1234)
        coverage_map.record_edge(0x5678)
        
        assert coverage_map.get_edge_count() > 0
        
        # Reset
        coverage_map.reset()
        
        assert coverage_map.get_edge_count() == 0
        assert coverage_map.prev_location == 0

    def test_record_edge_basic(self, coverage_map):
        """Test recording a single edge"""
        coverage_map.record_edge(0x1234)
        
        assert coverage_map.get_edge_count() > 0

    def test_record_edge_sequence(self, coverage_map):
        """Test recording edge sequence"""
        # Record A -> B -> C
        coverage_map.record_edge(0x1111)  # A
        coverage_map.record_edge(0x2222)  # B
        coverage_map.record_edge(0x3333)  # C
        
        edge_count = coverage_map.get_edge_count()
        assert edge_count >= 2  # At least A->B and B->C

    def test_hit_count_saturation(self, coverage_map):
        """Test hit count saturates at 255"""
        location = 0x1234
        
        # Hit same edge 300 times
        for _ in range(300):
            coverage_map.record_edge(location)
            coverage_map.prev_location = 0  # Reset to hit same edge
        
        # Should saturate at 255
        assert max(coverage_map.bitmap) == 255

    def test_has_new_coverage_first_run(self, coverage_map):
        """Test new coverage on first run"""
        coverage_map.record_edge(0x1234)
        
        has_new = coverage_map.has_new_coverage()
        assert has_new is True

    def test_has_new_coverage_repeat_run(self, coverage_map):
        """Test no new coverage on repeat"""
        coverage_map.record_edge(0x1234)
        coverage_map.has_new_coverage()
        coverage_map.update_virgin_map()
        
        # Reset and run again
        coverage_map.reset()
        coverage_map.record_edge(0x1234)
        
        has_new = coverage_map.has_new_coverage()
        assert has_new is False

    def test_has_new_coverage_new_bucket(self, coverage_map):
        """Test new coverage with different hit count bucket"""
        # Hit once
        coverage_map.record_edge(0x1234)
        coverage_map.has_new_coverage()
        coverage_map.update_virgin_map()
        
        # Reset and hit multiple times (different bucket)
        coverage_map.reset()
        for _ in range(10):
            coverage_map.record_edge(0x1234)
            coverage_map.prev_location = 0
        
        has_new = coverage_map.has_new_coverage()
        assert has_new is True  # New bucket

    def test_update_virgin_map(self, coverage_map):
        """Test updating virgin map"""
        coverage_map.record_edge(0x1234)
        
        assert coverage_map.has_new_coverage() is True
        
        coverage_map.update_virgin_map()
        
        assert coverage_map.total_edges_found > 0

    def test_count_class_buckets(self, coverage_map):
        """Test hit count classification"""
        assert coverage_map._count_class(0) == 0
        assert coverage_map._count_class(1) == 1
        assert coverage_map._count_class(2) == 2
        assert coverage_map._count_class(3) == 4
        assert coverage_map._count_class(5) == 8  # 4-7
        assert coverage_map._count_class(10) == 16  # 8-15
        assert coverage_map._count_class(20) == 32  # 16-31
        assert coverage_map._count_class(50) == 64  # 32-127
        assert coverage_map._count_class(200) == 128  # 128+

    def test_classify_counts(self, coverage_map):
        """Test bitmap classification"""
        coverage_map.record_edge(0x1234)
        
        classified = coverage_map.classify_counts()
        
        assert len(classified) == coverage_map.MAP_SIZE
        assert isinstance(classified, bytearray)

    def test_edge_count(self, coverage_map):
        """Test edge counting"""
        assert coverage_map.get_edge_count() == 0
        
        coverage_map.record_edge(0x1234)
        coverage_map.record_edge(0x5678)
        
        assert coverage_map.get_edge_count() >= 1
