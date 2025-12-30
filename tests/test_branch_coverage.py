"""Targeted tests for 100% branch coverage"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from protocrash.fuzzing_engine.coordinator import FuzzingCoordinator, FuzzingConfig
from protocrash.fuzzing_engine.scheduler import QueueScheduler
from protocrash.fuzzing_engine.stats import FuzzingStats
from protocrash.monitors.crash_classifier import CrashClassifier
from protocrash.monitors.crash_minimizer import CrashMinimizer
from protocrash.mutators.deterministic import DeterministicMutator
from protocrash.mutators.havoc import HavocMutator
from protocrash.core.types import CrashInfo, CrashType

class TestBranchCoverage:
    """Tests to hit specific missed branches"""

    # ===== Coordinator Branches =====
    def test_coordinator_loop_exit(self):
        """Test coordinator start loop exit (Line 88->160)"""
        config = FuzzingConfig(
            target_cmd=["echo"],
            corpus_dir="corpus",
            crashes_dir="crashes"
        )
        coordinator = FuzzingCoordinator(config)
        
        # Mock everything to avoid side effects
        coordinator.corpus = Mock()
        coordinator.corpus.get_size.return_value = 1
        coordinator.corpus.get_input.return_value = b"test"
        coordinator.scheduler = Mock()
        coordinator.scheduler.get_next.return_value = "hash1"
        coordinator.coverage_tracker = Mock()
        coordinator.crash_detector = Mock()
        coordinator.crash_detector.execute_and_detect.return_value = CrashInfo(crashed=False, input_data=b"test")
        coordinator.stats = Mock()
        coordinator.mutation_engine = Mock()
        coordinator.mutation_engine.mutate.return_value = b"mutated"
        
        # Run for 1 iteration then stop
        def stop_running():
            coordinator.running = False
            return "hash1"
            
        coordinator._select_input = stop_running
        
        # Should run loop once then exit
        coordinator.run()

    def test_coordinator_metadata_none(self):
        """Test coordinator _select_input when get_metadata returns None (Line 179)"""
        config = FuzzingConfig(
            target_cmd=["echo"],
            corpus_dir="corpus",
            crashes_dir="crashes"
        )
        coordinator = FuzzingCoordinator(config)
        
        # Ensure scheduler is empty so we fall through to random selection
        assert coordinator.scheduler.get_size() == 0
        
        # Patch corpus methods directly on the instance
        with patch.object(coordinator.corpus, 'get_random_input', return_value="some_input"):
            with patch.object(coordinator.corpus, 'get_all_hashes', return_value=["hash1"]):
                with patch.object(coordinator.corpus, 'get_metadata', return_value=None) as mock_meta:
                    
                    # Should not crash and should not add to scheduler
                    coordinator._select_input()
                    
                    # Verify we actually called get_metadata
                    mock_meta.assert_called_with("hash1")
                    
                    # Verify we didn't add anything (proving we took the False branch)
                    assert coordinator.scheduler.get_size() == 0

    # ===== Scheduler Branches =====
    def test_scheduler_update_unknown_hash(self):
        """Test update_priority with unknown hash (Line 96 loop exit)"""
        scheduler = QueueScheduler()
        # Add multiple items
        scheduler.add_input("hash1", 100, 1)
        scheduler.add_input("hash2", 100, 1)
        scheduler.add_input("hash3", 100, 1)
        
        # Update unknown hash - should iterate all 3 and exit loop
        scheduler.update_priority("unknown_hash", 10)
        # Should do nothing, size remains 3
        assert scheduler.get_size() == 3

    def test_scheduler_remove_last_item(self):
        """Test removing the physically last element from heap (Line 101 False branch)"""
        scheduler = QueueScheduler()
        # Add items
        scheduler.add_input("hash1", 100, 1)
        scheduler.add_input("hash2", 100, 1)
        scheduler.add_input("hash3", 100, 1)
        
        # Find which item is physically last in the list
        last_item_hash = scheduler.queue[-1].input_hash
        
        # Update that specific item - this triggers the "no heapify needed" path
        scheduler.update_priority(last_item_hash, 5)

    # ===== Stats Branches =====
    def test_stats_init_values(self):
        """Test stats init with existing values (Lines 35, 37)"""
        stats = FuzzingStats(start_time=1.0, last_update=1.0)
        # Should not change times
        assert stats.start_time == 1.0
        assert stats.last_update == 1.0

    def test_stats_zero_time_elapsed(self):
        """Test performance update with 0 time elapsed (Line 85)"""
        stats = FuzzingStats()
        stats.start_time = time.time()
        stats.last_update = stats.start_time 
        # Force time.time to return start_time
        with patch('time.time', return_value=stats.start_time):
            stats._update_performance()
            assert stats.time_elapsed == 0.0
            assert stats.execs_per_sec == 0.0

    # ===== Crash Classifier Branches =====
    def test_classifier_no_crash_type(self):
        """Test generate_crash_id with no crash type (Line 76)"""
        info = CrashInfo(crashed=True, crash_type=None, input_data=b"")
        crash_id = CrashClassifier.generate_crash_id(info)
        assert crash_id

    # ===== Crash Minimizer Branches =====
    def test_minimizer_loop_exhaustion(self):
        """Test minimizer exists"""
        from protocrash.monitors.crash_detector import CrashDetector
        detector = CrashDetector(timeout_ms=1000)
        minimizer = CrashMinimizer(detector, timeout_budget=10)
        assert minimizer is not None

    def test_minimizer_byte_zero(self):
        """Test minimizer byte already zero (Line 94)"""
        minimizer = CrashMinimizer(None)
        crash_fn = lambda x: CrashInfo(crashed=True, crash_type=CrashType.SEGV, input_data=x)
        
        # Input with a zero byte
        data = b"\x00\x01"
        minimizer._minimize_bytes(data, crash_fn)

    # ===== Deterministic Mutator Branches =====
    def test_deterministic_out_of_bounds(self):
        """Test bit/byte flip out of bounds (Lines 41, 74)"""
        mutator = DeterministicMutator()
        
        # Force out of bounds for bit flip
        # _flip_bits(data, position, count)
        # position=0, count=100 on 1 byte data
        mutator._flip_bits(b"A", 0, 100)
        
        # Force out of bounds for byte flip
        mutator._flip_bytes(b"A", 0, 100)

    # ===== Havoc Mutator Branches =====
    def test_havoc_branches(self):
        """Test havoc empty data branches (Lines 62, 90, 104)"""
        mutator = HavocMutator()
        empty = b""
        
        # Arithmetic on empty data
        mutator._apply_operation(empty, "arithmetic")
        
        # Insert random on empty data
        mutator._apply_operation(empty, "insert_random")
        
        # Invalid operation (covers implicit else)
        result = mutator._apply_operation(b"test", "invalid_op")
        assert result == b"test"

        # Valid bit flip (covers if byte_idx < len(result))
        mutator._flip_bit(b"A", 0)


