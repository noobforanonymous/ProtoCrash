"""Test fuzzing coordinator"""

import pytest
import tempfile
from pathlib import Path
from protocrash.fuzzing_engine.coordinator import FuzzingCoordinator, FuzzingConfig


class TestFuzzingCoordinator:
    """Test FuzzingCoordinator class"""

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
            target_cmd=["echo"],  # Simple target
            corpus_dir=corpus_dir,
            crashes_dir=crashes_dir,
            timeout_ms=1000,
            max_iterations=5,  # Run only 5 iterations
            stats_interval=1
        )

    @pytest.fixture
    def coordinator(self, config):
        """Create FuzzingCoordinator instance"""
        return FuzzingCoordinator(config)

    def test_init(self, coordinator, config):
        """Test initialization"""
        assert coordinator.config == config
        assert coordinator.iteration == 0
        assert coordinator.running is False

    def test_add_seed(self, coordinator):
        """Test adding seed"""
        coordinator.add_seed(b"test seed")
        
        assert coordinator.corpus.get_size() == 1
        assert coordinator.scheduler.get_size() == 1

    def test_add_multiple_seeds(self, coordinator):
        """Test adding multiple seeds"""
        coordinator.add_seed(b"seed1")
        coordinator.add_seed(b"seed2")
        coordinator.add_seed(b"seed3")
        
        assert coordinator.corpus.get_size() == 3
        assert coordinator.scheduler.get_size() == 3

    def test_run_without_seeds(self, coordinator):
        """Test running without seeds raises error"""
        with pytest.raises(ValueError, match="Corpus is empty"):
            coordinator.run()

    def test_run_with_max_iterations(self, coordinator):
        """Test running with max iterations"""
        coordinator.add_seed(b"test seed")
        
        # Run fuzzing (will stop after 5 iterations)
        coordinator.run()
        
        assert coordinator.iteration >= 3
        assert coordinator.stats.total_execs > 0

    def test_select_input(self, coordinator):
        """Test input selection"""
        coordinator.add_seed(b"seed1")
        coordinator.add_seed(b"seed2")
        
        # Select input
        input_hash = coordinator._select_input()
        
        assert input_hash is not None
        assert input_hash in coordinator.corpus.get_all_hashes()

    def test_select_input_empty_queue(self, coordinator):
        """Test input selection refills queue from corpus"""
        coordinator.add_seed(b"seed1")
        
        # Empty the queue
        coordinator.scheduler.clear()
        
        # Should refill from corpus
        input_hash = coordinator._select_input()
        assert input_hash is not None

    def test_update_stats(self, coordinator):
        """Test stats updating"""
        coordinator.add_seed(b"test")
        
        # Initial stats
        coordinator._update_stats()
        
        assert coordinator.stats.corpus_size > 0

    def test_integration_basic_fuzzing(self, coordinator):
        """Test basic fuzzing integration"""
        # Add seeds
        coordinator.add_seed(b"GET / HTTP/1.1\r\n")
        coordinator.add_seed(b"POST /test HTTP/1.1\r\n")
        
        # Run fuzzing
        coordinator.run()
        
        # Verify fuzzing ran
        assert coordinator.iteration >= 3
        assert coordinator.stats.total_execs == 5
        
        # Corpus may have grown with interesting inputs
        assert coordinator.corpus.get_size() >= 2
