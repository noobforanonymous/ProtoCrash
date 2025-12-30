"""Comprehensive tests for StatsAggregator"""

import pytest
import time
from unittest.mock import Mock
from protocrash.distributed.stats_aggregator import StatsAggregator, WorkerStats
from protocrash.fuzzing_engine.stats import FuzzingStats


class TestWorkerStats:
    """Test WorkerStats dataclass"""
    
    def test_worker_stats_init(self):
        """Test WorkerStats initialization"""
        worker = WorkerStats(worker_id=3)
        
        assert worker.worker_id == 3
        assert worker.executions == 0
        assert worker.crashes == 0
        assert worker.hangs == 0
        assert worker.timeouts == 0
        assert worker.corpus_size == 0
        assert worker.coverage_edges == 0
        assert worker.last_update > 0
        assert worker.start_time > 0
    
    def test_get_exec_per_sec(self):
        """Test executions per second calculation"""
        worker = WorkerStats(worker_id=0)
        worker.executions = 1000
        
        # Simulate 1 second elapsed
        worker.start_time = time.time() - 1.0
        exec_sec = worker.get_exec_per_sec()
        
        # Should be approximately 1000 exec/sec
        assert 900 < exec_sec < 1100
    
    def test_get_exec_per_sec_zero_elapsed(self):
        """Test exec/sec with zero elapsed time"""
        worker = WorkerStats(worker_id=0)
        # Very small elapsed time
        exec_sec = worker.get_exec_per_sec()
        # Should be very high due to near-zero elapsed time
        assert exec_sec >= 0
        # Very small elapsed time
        exec_sec = worker.get_exec_per_sec()
        # Should be very high due to near-zero elapsed time
        assert exec_sec >= 0
        # Very small elapsed time
        exec_sec = worker.get_exec_per_sec()
        # Should be very high due to near-zero elapsed time
        assert exec_sec >= 0
        # Very small elapsed time
        exec_sec = worker.get_exec_per_sec()
        # Should be very high due to near-zero elapsed time
        assert exec_sec >= 0
        # Very small elapsed time
        exec_sec = worker.get_exec_per_sec()
        # Should be very high due to near-zero elapsed time
        assert exec_sec >= 0


class TestStatsAggregator:
    """Test StatsAggregator class"""
    
    @pytest.fixture
    def aggregator(self):
        """Create StatsAggregator with 4 workers"""
        return StatsAggregator(num_workers=4)
    
    @pytest.fixture
    def mock_stats(self):
        """Create mock FuzzingStats"""
        stats = Mock(spec=FuzzingStats)
        stats.total_execs = 1000
        stats.unique_crashes = 5
        stats.unique_hangs = 2
        stats.timeouts = 1
        stats.corpus_size = 50
        stats.coverage_edges = 1234
        return stats
    
    def test_init(self):
        """Test initialization creates worker stats"""
        agg = StatsAggregator(num_workers=3)
        
        assert agg.num_workers == 3
        assert len(agg.worker_stats) == 3
        assert all(i in agg.worker_stats for i in range(3))
        assert agg.start_time > 0
    
    def test_update_worker_stats(self, aggregator, mock_stats):
        """Test updating worker statistics"""
        aggregator.update_worker_stats(worker_id=0, stats=mock_stats)
        
        worker = aggregator.worker_stats[0]
        assert worker.executions == 1000
        assert worker.crashes == 5
        assert worker.hangs == 2
        assert worker.timeouts == 1
        assert worker.corpus_size == 50
        assert worker.coverage_edges == 1234
    
    def test_update_nonexistent_worker(self, aggregator, mock_stats):
        """Test updating stats for worker not in initial list"""
        # Update worker 10 (not in initial 0-3)
        aggregator.update_worker_stats(worker_id=10, stats=mock_stats)
        
        assert 10 in aggregator.worker_stats
        assert aggregator.worker_stats[10].executions == 1000
    
    def test_get_aggregate_stats(self, aggregator, mock_stats):
        """Test aggregate statistics calculation"""
        # Update all 4 workers with same stats
        for i in range(4):
            aggregator.update_worker_stats(i, mock_stats)
        
        agg = aggregator.get_aggregate_stats()
        
        assert agg['total_executions'] == 4000  # 1000 * 4
        assert agg['total_crashes'] == 20       # 5 * 4
        assert agg['total_hangs'] == 8          # 2 * 4
        assert agg['total_timeouts'] == 4       # 1 * 4
        assert agg['total_corpus_size'] == 200  # 50 * 4
        assert agg['coverage_edges'] == 1234    # max, not sum
        assert agg['num_workers'] == 4
        assert agg['global_exec_per_sec'] > 0
        assert agg['elapsed_time'] > 0
    
    def test_get_aggregate_stats_empty(self):
        """Test aggregate stats with zero workers"""
        agg = StatsAggregator(num_workers=0)
        stats = agg.get_aggregate_stats()
        
        assert stats['total_executions'] == 0
        assert stats['total_crashes'] == 0
        assert stats['coverage_edges'] == 0
        assert stats['num_workers'] == 0
    
    def test_get_worker_breakdown(self, aggregator, mock_stats):
        """Test per-worker breakdown"""
        # Update workers with different stats
        for i in range(4):
            stats = Mock(spec=FuzzingStats)
            stats.total_execs = (i + 1) * 100
            stats.unique_crashes = i
            stats.unique_hangs = i
            stats.timeouts = 0
            stats.corpus_size = i * 10
            stats.coverage_edges = 1000
            aggregator.update_worker_stats(i, stats)
        
        breakdown = aggregator.get_worker_breakdown()
        
        assert len(breakdown) == 4
        assert breakdown[0]['worker_id'] == 0
        assert breakdown[0]['executions'] == 100
        assert breakdown[1]['executions'] == 200
        assert breakdown[3]['executions'] == 400
    
    def test_display_stats(self, aggregator, mock_stats, caplog):
        """Test display_stats logs to logger"""
        import logging
        caplog.set_level(logging.INFO)
        
        aggregator.update_worker_stats(0, mock_stats)
        
        aggregator.display_stats()
        
        # Check that logging output contains expected strings
        log_output = caplog.text
        assert "DISTRIBUTED FUZZING STATISTICS" in log_output
        assert "Workers:" in log_output
        assert "Total Execs:" in log_output
        assert "PER-WORKER BREAKDOWN" in log_output
    
    def test_get_inactive_workers(self, aggregator):
        """Test inactive worker detection"""
        # Update worker 0 recently, worker 1 long ago
        aggregator.worker_stats[0].last_update = time.time()
        aggregator.worker_stats[1].last_update = time.time() - 20  # 20 seconds ago
        
        inactive = aggregator.get_inactive_workers(timeout=10.0)
        
        assert 1 in inactive
        assert 0 not in inactive
    
    def test_get_inactive_workers_all_active(self, aggregator):
        """Test when all workers are active"""
        # Update all workers recently
        for worker in aggregator.worker_stats.values():
            worker.last_update = time.time()
        
        inactive = aggregator.get_inactive_workers(timeout=5.0)
        
        assert len(inactive) == 0
    
    def test_reset_stats(self, aggregator, mock_stats):
        """Test resetting all statistics"""
        # Update workers
        for i in range(4):
            aggregator.update_worker_stats(i, mock_stats)
        
        # Reset
        aggregator.reset_stats()
        
        # Verify all zeroed
        for worker in aggregator.worker_stats.values():
            assert worker.executions == 0
            assert worker.crashes == 0
            assert worker.hangs == 0
            assert worker.timeouts == 0
            assert worker.corpus_size == 0
            assert worker.coverage_edges == 0
    
    def test_coverage_edges_uses_max_not_sum(self, aggregator):
        """Test coverage edges uses max across workers, not sum"""
        # Workers with different coverage
        for i in range(4):
            stats = Mock(spec=FuzzingStats)
            stats.total_execs = 100
            stats.unique_crashes = 0
            stats.unique_hangs = 0
            stats.timeouts = 0
            stats.corpus_size = 10
            stats.coverage_edges = (i + 1) * 100  # 100, 200, 300, 400
            aggregator.update_worker_stats(i, stats)
        
        agg = aggregator.get_aggregate_stats()
        
        # Should be max (400), not sum (1000)
        assert agg['coverage_edges'] == 400
    
    def test_global_exec_per_sec_calculation(self, aggregator, mock_stats):
        """Test global exec/sec calculation"""
        # Simulate  1 second elapsed
        aggregator.start_time = time.time() - 1.0
        
        # Update all workers
        for i in range(4):
            aggregator.update_worker_stats(i, mock_stats)
        
        agg = aggregator.get_aggregate_stats()
        
        # 4000 execs in ~1 second
        assert 3000 < agg['global_exec_per_sec'] < 5000
    
    def test_worker_breakdown_sorted_by_id(self, aggregator, mock_stats):
        """Test worker breakdown is sorted by worker_id"""
        # Update workers in random order
        for i in [2, 0, 3, 1]:
            aggregator.update_worker_stats(i, mock_stats)
        
        breakdown = aggregator.get_worker_breakdown()
        
        # Should be sorted 0, 1, 2, 3
        assert [w['worker_id'] for w in breakdown] == [0, 1, 2, 3]
    
    def test_elapsed_time_in_aggregate_stats(self, aggregator):
        """Test elapsed_time is included in aggregate stats"""
        time.sleep(0.1)  # Small delay
        
        agg = aggregator.get_aggregate_stats()
        
        assert agg['elapsed_time'] > 0.09
        assert 'elapsed_time' in agg
    
    def test_last_update_timestamp_updated(self, aggregator, mock_stats):
        """Test last_update timestamp is set on update"""
        before = time.time()
        aggregator.update_worker_stats(0, mock_stats)
        after = time.time()
        
        assert before <= aggregator.worker_stats[0].last_update <= after
