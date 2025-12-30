"""Test fuzzing statistics"""

import pytest
import time
from protocrash.fuzzing_engine.stats import FuzzingStats


class TestFuzzingStats:
    """Test FuzzingStats class"""

    @pytest.fixture
    def stats(self):
        """Create FuzzingStats instance"""
        return FuzzingStats()

    def test_init(self, stats):
        """Test initialization"""
        assert stats.total_execs == 0
        assert stats.unique_crashes == 0
        assert stats.unique_hangs == 0
        assert stats.start_time > 0

    def test_increment_execs(self, stats):
        """Test incrementing executions"""
        stats.increment_execs()
        assert stats.total_execs == 1
        
        stats.increment_execs(5)
        assert stats.total_execs == 6

    def test_add_crash(self, stats):
        """Test adding crash"""
        stats.add_crash()
        assert stats.unique_crashes == 1
        
        stats.add_crash()
        assert stats.unique_crashes == 2

    def test_add_hang(self, stats):
        """Test adding hang"""
        stats.add_hang()
        assert stats.unique_hangs == 1

    def test_update_coverage(self, stats):
        """Test updating coverage"""
        stats.update_coverage(total_edges=500, max_edges=1000)
        
        assert stats.total_edges == 500
        assert stats.coverage_percent == 50.0

    def test_update_coverage_zero_max(self, stats):
        """Test coverage with zero max edges"""
        stats.update_coverage(total_edges=100, max_edges=0)
        assert stats.coverage_percent == 0.0

    def test_update_corpus_stats(self, stats):
        """Test updating corpus statistics"""
        stats.update_corpus_stats(corpus_size=50, queue_depth=10)
        
        assert stats.corpus_size == 50
        assert stats.queue_depth == 10

    def test_performance_metrics(self, stats):
        """Test performance metrics calculation"""
        stats.increment_execs(1000)
        
        # Let some time pass
        time.sleep(0.1)
        
        stats.increment_execs()
        
        assert stats.time_elapsed > 0
        assert stats.execs_per_sec > 0

    def test_get_formatted_stats(self, stats):
        """Test formatted stats display"""
        stats.total_execs = 1000
        stats.unique_crashes = 5
        stats.unique_hangs = 2
        stats.update_coverage(500, 1000)
        stats.update_corpus_stats(20, 10)
        
        formatted = stats.get_formatted_stats()
        
        assert "1000" in formatted
        assert "5" in formatted
        assert "50.00%" in formatted
        assert "FUZZING STATISTICS" in formatted

    def test_to_dict(self, stats):
        """Test exporting to dictionary"""
        stats.total_execs = 100
        stats.add_crash()
        
        data = stats.to_dict()
        
        assert isinstance(data, dict)
        assert data["total_execs"] == 100
        assert data["unique_crashes"] == 1
        assert "start_time" in data

    def test_reset(self, stats):
        """Test resetting statistics"""
        stats.total_execs = 1000
        stats.unique_crashes = 10
        stats.update_coverage(500, 1000)
        
        old_start_time = stats.start_time
        
        stats.reset()
        
        assert stats.total_execs == 0
        assert stats.unique_crashes == 0
        assert stats.total_edges == 0
        assert stats.start_time > old_start_time
