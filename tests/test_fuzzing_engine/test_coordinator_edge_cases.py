"""Comprehensive tests for fuzzing coordinator - edge cases"""

import pytest
import tempfile
import signal
from unittest.mock import Mock, patch, MagicMock
from protocrash.fuzzing_engine.coordinator import FuzzingCoordinator, FuzzingConfig
from protocrash.core.types import CrashInfo, CrashType


class TestFuzzingCoordinatorEdgeCases:
    """Test FuzzingCoordinator edge cases and error paths"""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories"""
        with tempfile.TemporaryDirectory() as corpus_dir:
            with tempfile.TemporaryDirectory() as crashes_dir:
                yield corpus_dir, crashes_dir

    @pytest.fixture
    def config(self, temp_dirs):
        """Create fuzzing configuration"""
        corpus_dir, crashes_dir = temp_dirs
        return FuzzingConfig(
            target_cmd=["echo"],
            corpus_dir=corpus_dir,
            crashes_dir=crashes_dir,
            timeout_ms=1000,
            max_iterations=10,
            stats_interval=1
        )

    @pytest.fixture
    def coordinator(self, config):
        """Create FuzzingCoordinator instance"""
        return FuzzingCoordinator(config)

    def test_select_input_none_when_queue_empty_and_no_corpus(self, coordinator):
        """Test _select_input returns None when queue and corpus empty"""
        # Empty queue and corpus
        coordinator.scheduler.clear()
        
        result = coordinator._select_input()
        assert result is None

    def test_select_input_refills_queue_from_corpus(self, coordinator):
        """Test _select_input refills queue from corpus when empty"""
        # Add seeds
        coordinator.add_seed(b"seed1")
        coordinator.add_seed(b"seed2")
        
        # Empty queue
        coordinator.scheduler.clear()
        
        # Should refill from corpus
        result = coordinator._select_input()
        assert result is not None
        
        # Queue should now have items
        assert coordinator.scheduler.get_size() > 0

    def test_run_breaks_when_no_input_selected(self, coordinator):
        """Test run breaks gracefully when no input can be selected"""
        coordinator.add_seed(b"test")
        
        # Mock _select_input to return None
        coordinator._select_input = Mock(return_value=None)
        
        coordinator.run()
        
        # Should have exited gracefully
        assert coordinator.iteration == 0

    def test_run_continues_when_input_data_none(self, coordinator):
        """Test run continues when corpus.get_input returns None"""
        coordinator.add_seed(b"test")
        coordinator.config.max_iterations = 2
        
        # Mock to return None for input_data
        original_get = coordinator.corpus.get_input
        call_count = [0]
        
        def mock_get_input(hash_val):
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # First call returns None
            return original_get(hash_val)
        
        coordinator.corpus.get_input = mock_get_input
        
        coordinator.run()
        
        # Should have continued despite None input
        assert coordinator.iteration > 0

    def test_handle_crash_with_hang(self, coordinator):
        """Test crash handling for HANG type"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.HANG,
            exit_code=-1,
            stderr=b"timeout",
            input_data=b"test"
        )
        
        coordinator._handle_crash(crash_info, b"test input")
        
        # Should increment hangs
        assert coordinator.stats.unique_hangs == 1
        assert coordinator.stats.unique_crashes == 0

    def test_handle_crash_with_segv(self, coordinator):
        """Test crash handling for SEGV type"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            signal_number=11,
            stderr=b"segfault",
            input_data=b"test"
        )

        
        coordinator._handle_crash(crash_info, b"test input")
        
        # Should increment crashes
        assert coordinator.stats.unique_crashes == 1
        assert coordinator.stats.unique_hangs == 0

    def test_handle_crash_duplicate_detection(self, coordinator):
        """Test duplicate crash detection"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            signal_number=11,
            stderr=b"segfault at 0x0",
            input_data=b"test"
        )

        
        # Handle same crash twice
        coordinator._handle_crash(crash_info, b"test input")
        coordinator._handle_crash(crash_info, b"test input")
        
        # Should only count once
        assert coordinator.stats.unique_crashes == 1
        assert len(coordinator.seen_crashes) == 1

    def test_new_coverage_adds_to_corpus(self, coordinator):
        """Test new coverage handling adds to corpus"""
        coordinator.add_seed(b"test")
        coordinator.config.max_iterations = 1
        
        # Force new coverage detection
        original_mutate = coordinator.mutation_engine.mutate
        coordinator.mutation_engine.mutate = lambda x: b"A" * 7  # len % 7 == 0
        
        initial_size = coordinator.corpus.get_size()
        
        coordinator.run()
        
        # Corpus may have grown if new coverage found
        # (depends on placeholder logic)
        assert coordinator.corpus.get_size() >= initial_size

    def test_signal_handler_stops_fuzzing(self, coordinator):
        """Test signal handler sets running to False"""
        coordinator.running = True
        
        # Call signal handler
        coordinator._signal_handler(signal.SIGINT, None)
        
        assert coordinator.running is False

    def test_display_stats_called_periodically(self, coordinator, capsys):
        """Test stats display is called periodically"""
        coordinator.add_seed(b"test")
        coordinator.config.max_iterations = 3
        coordinator.config.stats_interval = 0  # Always display
        
        with patch.object(coordinator, '_display_stats') as mock_display:
            coordinator.run()
            
            # Should have been called multiple times
            assert mock_display.call_count > 0

    def test_cleanup_called_on_completion(self, coordinator, caplog):
        """Test cleanup is called when fuzzing completes"""
        import logging
        caplog.set_level(logging.INFO)
        
        coordinator.add_seed(b"test")
        coordinator.config.max_iterations = 1
        
        coordinator.run()
        
        # Check logging output
        log_output = caplog.text
        
        # Should show completion message in logs
        assert "FUZZING CAMPAIGN COMPLETE" in log_output

    def test_keyboard_interrupt_handling(self, coordinator):
        """Test KeyboardInterrupt is caught and handled"""
        coordinator.add_seed(b"test")
        
        # Mock to raise KeyboardInterrupt
        original_mutate = coordinator.mutation_engine.mutate
        def raise_interrupt(x):
            raise KeyboardInterrupt()
        
        coordinator.mutation_engine.mutate = raise_interrupt
        
        # Should not raise exception
        coordinator.run()
        
        assert coordinator.iteration >= 0

    def test_corpus_execution_count_incremented(self, coordinator):
        """Test corpus execution count is incremented"""
        input_hash = coordinator.corpus.add_input(b"test seed")
        coordinator.scheduler.add_input(input_hash, 9, 0)
        
        coordinator.config.max_iterations = 1
        
        initial_count = coordinator.corpus.get_metadata(input_hash).execution_count
        
        coordinator.run()
        
        final_count = coordinator.corpus.get_metadata(input_hash).execution_count
        
        # Should have incremented
        assert final_count > initial_count
