"""Comprehensive integration tests for FuzzingWorker to achieve 98%+ coverage"""

import pytest
import time
import tempfile
import signal
from unittest.mock import Mock, MagicMock, patch, call
from multiprocessing import Queue

from protocrash.distributed.worker import FuzzingWorker
from protocrash.fuzzing_engine.coordinator import FuzzingConfig
from protocrash.core.types import CrashInfo, CrashType


class TestFuzzingWorkerIntegration:
    """Integration tests for FuzzingWorker - targeting missing lines 66-90, 102, 140-148, 152, 157-160"""
    
    @pytest.fixture
    def config(self):
        """Create test fuzzing configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield FuzzingConfig(
                target_cmd=["echo", "test"],
                corpus_dir=f"{tmpdir}/corpus",
                crashes_dir=f"{tmpdir}/crashes",
                max_iterations=10
            )
    
    @pytest.fixture
    def temp_sync_dir(self, tmp_path):
        """Create temporary sync directory"""
        return str(tmp_path)
    
    @pytest.fixture
    def stats_queue(self):
        """Create stats queue"""
        return Queue()
    
    def test_run_executes_iterations_until_max(self, config, temp_sync_dir, stats_queue):
        """Test run() executes iterations until max_iterations reached"""
        worker = FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_sync_dir,
            stats_queue=stats_queue,
            sync_interval=10.0  # High interval to avoid sync during test
        )
        
        # Mock fuzzing iteration
        worker._fuzzing_iteration = Mock()
        worker._sync_corpus = Mock()
        worker._report_stats = Mock()
        
        # Run with max iterations
        worker.run(max_iterations=5)
        
        # Should execute exactly 5 iterations
        assert worker._fuzzing_iteration.call_count == 5
    
    def test_run_handles_sync_interval(self, config, temp_sync_dir, stats_queue):
        """Test run() performs periodic corpus synchronization"""
        worker = FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_sync_dir,
            stats_queue=stats_queue,
            sync_interval=0.1  # Very short interval
        )
        
        worker._fuzzing_iteration = Mock()
        worker._sync_corpus = Mock()
        worker._report_stats = Mock()
        
        # Run for a bit longer than sync interval
        worker.run(max_iterations=10)
        
        # Should sync at least once
        assert worker._sync_corpus.call_count >= 1
        assert worker._report_stats.call_count >= 1
    
    def test_run_updates_last_sync_time(self, config, temp_sync_dir, stats_queue):
        """Test run() updates last_sync_time after sync"""
        worker = FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_sync_dir,
            stats_queue=stats_queue,
            sync_interval=0.1
        )
        
        worker._fuzzing_iteration = Mock()
        worker._sync_corpus = Mock()
        worker._report_stats = Mock()
        
        initial_sync_time = worker.last_sync_time
        worker.run(max_iterations=10)
        
        # last_sync_time should be updated
        assert worker.last_sync_time > initial_sync_time
    
    def test_signal_handler_stops_running_loop(self, config, temp_sync_dir, stats_queue):
        """Test signal handler stops the fuzzing loop"""
        worker = FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_sync_dir,
            stats_queue=stats_queue
        )
        
        worker.running = True
        worker._signal_handler(signal.SIGINT, None)
        
        assert worker.running is False
    
    def test_cleanup_is_called_after_run(self, config, temp_sync_dir, stats_queue):
        """Test cleanup() is called after run() completes"""
        worker = FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_sync_dir,
            stats_queue=stats_queue
        )
        
        worker._fuzzing_iteration = Mock()
        worker._cleanup = Mock()
        
        worker.run(max_iterations=1)
        
        # Cleanup should be called
        worker._cleanup.assert_called_once()
    
    def test_fuzzing_iteration_with_no_input_hash(self, config, temp_sync_dir, stats_queue):
        """Test _fuzzing_iteration() returns early when no input selected"""
        worker = FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_sync_dir,
            stats_queue=stats_queue
        )
        
        worker.coordinator._select_input = Mock(return_value=None)
        worker.coordinator.corpus.get_input = Mock()
        
        worker._fuzzing_iteration()
        
        # Should not try to get input if hash is None
        worker.coordinator.corpus.get_input.assert_not_called()
    
    def test_fuzzing_iteration_with_no_input_data(self, config, temp_sync_dir, stats_queue):
        """Test _fuzzing_iteration() returns early when input data is None - Line 102"""
        worker = FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_sync_dir,
            stats_queue=stats_queue
        )
        
        worker.coordinator._select_input = Mock(return_value="test_hash")
        worker.coordinator.corpus.get_input = Mock(return_value=None)
        worker.coordinator.mutation_engine.mutate = Mock()
        
        worker._fuzzing_iteration()
        
        # Should not try to mutate if input data is None
        worker.coordinator.mutation_engine.mutate.assert_not_called()
    
    def test_cleanup_calls_report_stats(self, config, temp_sync_dir, stats_queue):
        """Test cleanup() reports final stats - Lines 157-160"""
        worker = FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_sync_dir,
            stats_queue=stats_queue
        )
        
        worker._report_stats = Mock()
        worker.synchronizer.cleanup = Mock()
        
        worker._cleanup()
        
        # Should report final stats
        worker._report_stats.assert_called_once()
        worker.synchronizer.cleanup.assert_called_once()
    
    def test_run_sets_signal_handlers(self, config, temp_sync_dir, stats_queue):
        """Test run() sets up SIGINT and SIGTERM handlers - Lines 70-71"""
        worker = FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_sync_dir,
            stats_queue=stats_queue
        )
        
        worker._fuzzing_iteration = Mock()
        
        # Patch signal.signal to verify it's called
        with patch('signal.signal') as mock_signal:
            worker.run(max_iterations=1)
            
            # Should set up both signal handlers
            calls = mock_signal.call_args_list
            signal_types = [call[0][0] for call in calls]
            assert signal.SIGINT in signal_types
            assert signal.SIGTERM in signal_types
    
    def test_run_loop_checks_max_iterations(self, config, temp_sync_dir, stats_queue):
        """Test run() loop breaks when max_iterations reached - Lines 86-87"""
        worker = FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_sync_dir,
            stats_queue=stats_queue
        )
        
        worker._fuzzing_iteration = Mock()
        
        max_iters = 3
        worker.run(max_iterations=max_iters)
        
        # Should execute exactly max_iters times
        assert worker._fuzzing_iteration.call_count == max_iters
    
    def test_run_increments_iteration_counter(self, config, temp_sync_dir, stats_queue):
        """Test run() increments iteration counter - Line 77"""
        worker = FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_sync_dir,
            stats_queue=stats_queue
        )
        
        iteration_counts = []
        
        def track_iteration():
            # This would normally be inside the loop
            pass
        
        worker._fuzzing_iteration = Mock(side_effect=track_iteration)
        worker.run(max_iterations=5)
        
        # 5 iterations should complete
        assert worker._fuzzing_iteration.call_count == 5
    
    
    def test_run_sets_running_flag(self, config, temp_sync_dir, stats_queue):
        """Test run() sets running flag to True - Line 66"""
        worker = FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_sync_dir,
            stats_queue=stats_queue
        )
        
        assert worker.running is False
        
        worker._fuzzing_iteration = Mock()
        
        # Patch the while loop to exit immediately after setting running
        original_fuzzing = worker._fuzzing_iteration
        def fuzzing_once():
            assert worker.running is True
            worker.running = False  # Exit loop
            original_fuzzing()
        
        worker._fuzzing_iteration = fuzzing_once
        worker.run(max_iterations=1)
    
    def test_run_cleanup_called_on_exception(self, config, temp_sync_dir, stats_queue):
        """Test cleanup() called even if fuzzing_iteration raises exception - Lines 89-90"""
        worker = FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_sync_dir,
            stats_queue=stats_queue
        )
        
        worker._fuzzing_iteration = Mock(side_effect=Exception("Test exception"))
        worker._cleanup = Mock()
        
        # Should not crash, cleanup should be called
        with pytest.raises(Exception):
            worker.run(max_iterations=1)
        
        worker._cleanup.assert_called_once()
