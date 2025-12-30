"""Basic tests for DistributedCoordinator"""

import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
import multiprocessing as mp
import time

from protocrash.distributed.coordinator import DistributedCoordinator
from protocrash.fuzzing_engine.coordinator import FuzzingConfig
from protocrash.fuzzing_engine.stats import FuzzingStats


class TestDistributedCoordinator:
    """Test DistributedCoordinator class"""
    
    @pytest.fixture
    def config(self):
        """Create fuzzing configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield FuzzingConfig(
                target_cmd=["echo"],
                corpus_dir=f"{tmpdir}/corpus",
                crashes_dir=f"{tmpdir}/crashes",
                max_iterations=5
            )
    
    def test_init(self, config):
        """Test coordinator initialization"""
        coord = DistributedCoordinator(config, num_workers=2)
        
        assert coord.num_workers == 2
        assert coord.sync_interval == 5.0
        assert coord.sync_dir is not None
        assert coord.stats_queue is not None
        assert coord.aggregator is not None
        assert coord.running is False
        assert len(coord.workers) == 0
    
    def test_init_default_workers(self, config):
        """Test default worker count is CPU count"""
        coord = DistributedCoordinator(config)
        
        assert coord.num_workers == mp.cpu_count()
    
    def test_init_custom_sync_interval(self, config):
        """Test custom sync interval"""
        coord = DistributedCoordinator(config, sync_interval=10.0)
        
        assert coord.sync_interval == 10.0
    
    def test_add_seed(self, config):
        """Test add_seed method"""
        coord = DistributedCoordinator(config)
        
        # Should not crash (implementation is stub)
        coord.add_seed(b"test seed")
    
    @patch('protocrash.distributed.coordinator.mp.Process')
    def test_spawn_workers(self, mock_process_class, config):
        """Test worker spawning"""
        coord = DistributedCoordinator(config, num_workers=2)
        
        # Mock process instances
        mock_proc1 = Mock()
        mock_proc2 = Mock()
        mock_process_class.side_effect = [mock_proc1, mock_proc2]
        
        coord._spawn_workers()
        
        # Should create 2 processes
        assert mock_process_class.call_count == 2
        mock_proc1.start.assert_called_once()
        mock_proc2.start.assert_called_once()
        assert len(coord.workers) == 2
    
    def test_collect_stats(self, config):
        """Test stats collection from queue"""
        coord = DistributedCoordinator(config, num_workers=1)
        
        # Add mock stats to queue
        stats = FuzzingStats()
        stats.total_execs = 100
        stats.unique_crashes = 5
        
        coord.stats_queue.put({
            'worker_id': 0,
            'stats': stats
        })
        
        # Small delay to ensure queue is ready
        time.sleep(0.01)
        
        # Collect stats
        coord._collect_stats()
        
        # Verify stats were collected
        agg_stats = coord.aggregator.get_aggregate_stats()
        assert agg_stats['total_executions'] == 100
        assert agg_stats['total_crashes'] == 5
    
    def test_collect_stats_empty_queue(self, config):
        """Test stats collection with empty queue"""
        coord = DistributedCoordinator(config, num_workers=1)
        
        # Should not crash with empty queue
        coord._collect_stats()
    
    @patch('protocrash.distributed.coordinator.mp.Process')
    def test_cleanup(self, mock_process_class, config):
        """Test cleanup and worker termination"""
        coord = DistributedCoordinator(config, num_workers=2)
        
        # Create mock processes
        mock_proc1 = Mock()
        mock_proc1.is_alive.return_value = True
        mock_proc2 = Mock()
        mock_proc2.is_alive.return_value = False
        
        coord.workers = [mock_proc1, mock_proc2]
        coord.running = True
        
        # Run cleanup
        coord._cleanup()
        
        # Verify cleanup
        assert coord.running is False
        mock_proc1.terminate.assert_called_once()
        mock_proc1.join.assert_called()
        mock_proc2.terminate.assert_not_called()  # Already dead
    
    @patch('protocrash.distributed.coordinator.mp.Process')
    def test_cleanup_force_kill(self, mock_process_class, config):
        """Test cleanup force kills stubborn processes"""
        coord = DistributedCoordinator(config, num_workers=1)
        
        # Create mock process that won't die
        mock_proc = Mock()
        mock_proc.is_alive.side_effect = [True, True]  # Still alive after terminate
        
        coord.workers = [mock_proc]
        coord._cleanup()
        
        # Should call kill after terminate fails
        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()
    
    @patch('protocrash.distributed.coordinator.mp.Process')
    @patch('time.sleep')
    def test_run_with_duration(self, mock_sleep, mock_process_class, config):
        """Test run with duration limit"""
        coord = DistributedCoordinator(config, num_workers=1)
        
        # Mock process
        mock_proc = Mock()
        mock_proc.is_alive.return_value = True
        mock_process_class.return_value = mock_proc
        
        # Run for short duration
        coord.run(duration=0.1)
        
        # Verify workers were spawned
        assert len(coord.workers) == 1
        mock_proc.start.assert_called_once()
    
    @patch('protocrash.distributed.coordinator.mp.Process')
    def test_run_cleanup_on_exception(self, mock_process_class, config):
        """Test cleanup is called even on exception"""
        coord = DistributedCoordinator(config, num_workers=1)
        
        # Mock process
        mock_proc = Mock()
        mock_proc.is_alive.return_value = True
        mock_process_class.return_value = mock_proc
        
        # Make _collect_stats raise exception
        with patch.object(coord, '_collect_stats', side_effect=KeyboardInterrupt):
            try:
                coord.run(duration=1.0)
            except KeyboardInterrupt:
                pass
        
        # Cleanup should still be called
        assert coord.running is False
        mock_proc.terminate.assert_called()
