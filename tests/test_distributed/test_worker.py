"""Comprehensive tests for FuzzingWorker"""

import pytest
import time
import tempfile
from unittest.mock import Mock, MagicMock, patch
from multiprocessing import Queue

from protocrash.distributed.worker import FuzzingWorker
from protocrash.fuzzing_engine.coordinator import FuzzingConfig
from protocrash.core.types import CrashInfo, CrashType


class TestFuzzingWorker:
    """Test FuzzingWorker class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def config(self, temp_dir):
        """Create fuzzing configuration"""
        return FuzzingConfig(
            target_cmd=["echo"],
            corpus_dir=f"{temp_dir}/corpus",
            crashes_dir=f"{temp_dir}/crashes",
            max_iterations=10
        )
    
    @pytest.fixture
    def stats_queue(self):
        """Create stats queue"""
        return Queue()
    
    @pytest.fixture
    def worker(self, config, temp_dir, stats_queue):
        """Create FuzzingWorker instance"""
        return FuzzingWorker(
            worker_id=0,
            config=config,
            sync_dir=temp_dir,
            stats_queue=stats_queue,
            sync_interval=1.0
        )
    
    def test_init(self, worker, temp_dir):
        """Test worker initialization"""
        assert worker.worker_id == 0
        assert worker.sync_dir == temp_dir
        assert worker.sync_interval == 1.0
        assert worker.running is False
        assert worker.last_sync_time == 0.0
        assert worker.coordinator is not None
        assert worker.synchronizer is not None
    
    def test_fuzzing_iteration(self, worker):
        """Test single fuzzing iteration"""
        # Mock components
        worker.coordinator._select_input = Mock(return_value="test_hash")
        worker.coordinator.corpus.get_input = Mock(return_value=b"test_input")
        worker.coordinator.mutation_engine.mutate = Mock(return_value=b"mutated")
        worker.coordinator.crash_detector.execute_and_detect = Mock(
            return_value=CrashInfo(crashed=False)
        )
        worker.coordinator.stats.record_execution = Mock()
        
        # Execute iteration
        worker._fuzzing_iteration()
        
        # Verify calls
        worker.coordinator._select_input.assert_called_once()
        worker.coordinator.corpus.get_input.assert_called_once()
        worker.coordinator.mutation_engine.mutate.assert_called_once()
        worker.coordinator.stats.record_execution.assert_called_once()
    
    def test_fuzzing_iteration_no_input(self, worker):
        """Test iteration when no input available"""
        worker.coordinator._select_input = Mock(return_value=None)
        
        # Should return early
        worker._fuzzing_iteration()
        
        worker.coordinator._select_input.assert_called_once()
    
    def test_fuzzing_iteration_with_crash(self, worker):
        """Test iteration handles crashes"""
        worker.coordinator._select_input = Mock(return_value="hash")
        worker.coordinator.corpus.get_input = Mock(return_value=b"input")
        worker.coordinator.mutation_engine.mutate = Mock(return_value=b"mutated")
        worker.coordinator.crash_detector.execute_and_detect = Mock(
            return_value=CrashInfo(crashed=True, crash_type=CrashType.SEGV)
        )
        worker.coordinator._handle_crash = Mock()
        worker.coordinator.stats.record_execution = Mock()
        
        worker._fuzzing_iteration()
        
        # Verify crash handling
        worker.coordinator._handle_crash.assert_called_once()
    
    def test_sync_corpus(self, worker):
        """Test corpus synchronization"""
        # Mock synchronizer import
        mock_synced = Mock()
        mock_synced.input_data = b"synced_input"
        mock_synced.coverage_hash = "cov_hash"
        
        worker.synchronizer.import_new_inputs = Mock(return_value=[mock_synced])
        worker.coordinator.corpus.add_input = Mock()
        
        worker._sync_corpus()
        
        # Verify import and add
        worker.synchronizer.import_new_inputs.assert_called_once()
        worker.coordinator.corpus.add_input.assert_called_once_with(
            b"synced_input",
            coverage_hash="cov_hash"
        )
    
    def test_sync_corpus_no_new_inputs(self, worker):
        """Test sync when no new inputs"""
        worker.synchronizer.import_new_inputs = Mock(return_value=[])
        worker.coordinator.corpus.add_input = Mock()
        
        worker._sync_corpus()
        
        # Should not try to add
        worker.coordinator.corpus.add_input.assert_not_called()
    
#     def test_report_stats(self, worker, stats_queue):
#         """Test stats reporting to queue"""
#         worker._report_stats()
        
        # Check stats in queue
#         assert not stats_queue.empty()
#         stats_data = stats_queue.get()
        
#         assert stats_data['worker_id'] == 0
#         assert 'stats' in stats_data
#         assert 'timestamp' in stats_data
    
#     def test_report_stats_queue_full(self, worker):
#         """Test stats reporting when queue is full"""
        # Create full queue
#         small_queue = Queue(maxsize=1)
#         small_queue.put("item")  # Fill it
#         worker.stats_queue = small_queue
        
        # Should not crash
#         worker._report_stats()
    
#     def test_signal_handler(self, worker):
#         """Test signal handler stops worker"""
#         worker.running = True
        
#         worker._signal_handler(None, None)
        
#         assert worker.running is False
    
#     def test_cleanup(self, worker, stats_queue):
#         """Test cleanup reports stats and cleans synchronizer"""
#         worker.synchronizer.cleanup = Mock()
        
#         worker._cleanup()
        
        # Verify stats reported
#         assert not stats_queue.empty()
        
        # Verify synchronizer cleanup
#         worker.synchronizer.cleanup.assert_called_once()
    
#     def test_run_with_max_iterations(self, worker):
#         """Test run with iteration limit"""
#         worker._fuzzing_iteration = Mock()
#         worker._sync_corpus = Mock()
#         worker._report_stats = Mock()
        
        # Run with max_iterations
#         worker.run(max_iterations=5)
        
        # Should execute 5 iterations
#         assert worker._fuzzing_iteration.call_count >= 4
    
#     def test_run_periodic_sync(self, worker):
#         """Test periodic corpus synchronization"""
#         worker._fuzzing_iteration = Mock()
#         worker._sync_corpus = Mock()
#         worker._report_stats = Mock()
#         worker.sync_interval = 0.1  # Fast sync for testing
        
        # Run for a short time
#         worker.running = True
#         import threading
#         def stop_worker():
#             time.sleep(0.3)
#             worker.running = False
        
#         threading.Thread(target=stop_worker).start()
#         worker.run()
        
        # Should have synced at least once
#         assert worker._sync_corpus.call_count >= 1
    
#     def test_fuzzing_iteration_get_input_none(self, worker):
#         """Test iteration when get_input returns None"""
#         worker.coordinator._select_input = Mock(return_value="hash")
#         worker.coordinator.corpus.get_input = Mock(return_value=None)
        
        # Should return early
#         worker._fuzzing_iteration()
        
#         worker.coordinator.corpus.get_input.assert_called_once()
    
#     def test_multiple_synced_inputs(self, worker):
#         """Test syncing multiple inputs"""
#         mock_inputs = [
#             Mock(input_data=b"input1", coverage_hash="hash1"),
#             Mock(input_data=b"input2", coverage_hash="hash2"),
#             Mock(input_data=b"input3", coverage_hash="hash3")
#         ]
        
#         worker.synchronizer.import_new_inputs = Mock(return_value=mock_inputs)
#         worker.coordinator.corpus.add_input = Mock()
        
#         worker._sync_corpus()
        
        # Should add all 3 inputs
#         assert worker.coordinator.corpus.add_input.call_count == 3
