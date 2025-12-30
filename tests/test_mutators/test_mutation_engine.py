"""Test mutation engine"""

import pytest
from protocrash.mutators.mutation_engine import MutationEngine, MutationConfig


class TestMutationEngine:
    """Test MutationEngine class"""

    @pytest.fixture
    def engine(self):
        return MutationEngine()

    @pytest.fixture
    def sample_data(self):
        return b"TEST_DATA"

    def test_init_default_config(self, engine):
        """Test initialization with default config"""
        assert engine.config is not None
        assert engine.config.deterministic_enabled is True
        assert engine.config.havoc_enabled is True
        assert engine.deterministic is not None
        assert engine.havoc is not None

    def test_mutate_auto_strategy(self, engine, sample_data):
        """Test mutation with auto strategy selection"""
        mutated = engine.mutate(sample_data, strategy="auto")

        assert isinstance(mutated, bytes)
        # Should be different from original (with high probability)

    def test_mutate_bit_flip(self, engine, sample_data):
        """Test bit flip strategy"""
        mutated = engine.mutate(sample_data, strategy="bit_flip")

        assert isinstance(mutated, bytes)
        assert len(mutated) == len(sample_data)

    def test_mutate_havoc(self, engine, sample_data):
        """Test havoc strategy"""
        mutated = engine.mutate(sample_data, strategy="havoc")

        assert isinstance(mutated, bytes)

    def test_mutate_dictionary(self, engine, sample_data):
        """Test dictionary strategy"""
        mutated = engine.mutate(sample_data, strategy="dictionary")

        assert isinstance(mutated, bytes)
        # Should have injected something
        assert len(mutated) >= len(sample_data)

    def test_mutate_splice_no_corpus(self, engine, sample_data):
        """Test splice strategy without corpus"""
        mutated = engine.mutate(sample_data, strategy="splice")

        # Without corpus, should return original
        assert mutated == sample_data

    def test_mutate_splice_with_corpus(self, engine, sample_data):
        """Test splice strategy with corpus"""
        engine.set_corpus([b"CORPUS1", b"CORPUS2"])
        mutated = engine.mutate(sample_data, strategy="splice")

        assert isinstance(mutated, bytes)

    def test_mutate_batch(self, engine, sample_data):
        """Test batch mutation"""
        mutations = engine.mutate_batch(sample_data, count=10)

        assert len(mutations) == 10
        assert all(isinstance(m, bytes) for m in mutations)

    def test_empty_input(self, engine):
        """Test mutation on empty input"""
        mutated = engine.mutate(b"")
        assert mutated == b""

    def test_update_effectiveness(self, engine):
        """Test effectiveness tracking"""
        engine.update_effectiveness("havoc", found_coverage=True)
        engine.update_effectiveness("havoc", found_coverage=False)

        stats = engine.get_stats()
        assert "havoc" in stats
        assert stats["havoc"]["attempts"] == 2
        assert stats["havoc"]["successes"] == 1

    def test_strategy_weight_adjustment(self, engine):
        """Test that weights adjust based on success"""
        initial_weight = engine.config.mutation_weights["havoc"]

        engine.update_effectiveness("havoc", found_coverage=True)

        # Weight should increase after success
        assert engine.config.mutation_weights["havoc"] >= initial_weight

    def test_mutate_deterministic_strategy(self, engine, sample_data):
        """Test deterministic strategy (calls _mutate_deterministic)"""
        mutated = engine.mutate(sample_data, strategy="deterministic")

        assert isinstance(mutated, bytes)
        assert len(mutated) == len(sample_data)

    def test_mutate_arithmetic_strategy(self, engine, sample_data):
        """Test arithmetic strategy explicitly"""
        mutated = engine.mutate(sample_data, strategy="arithmetic")

        assert isinstance(mutated, bytes)

    def test_mutate_interesting_strategy(self, engine, sample_data):
        """Test interesting values strategy explicitly"""
        mutated = engine.mutate(sample_data, strategy="interesting")

        assert isinstance(mutated, bytes)

    def test_mutate_byte_flip_strategy(self, engine, sample_data):
        """Test byte flip strategy"""
        mutated = engine.mutate(sample_data, strategy="byte_flip")

        assert isinstance(mutated, bytes)
        assert len(mutated) == len(sample_data)

    def test_mutate_invalid_strategy(self, engine, sample_data):
        """Test that invalid strategy raises ValueError"""
        with pytest.raises(ValueError, match="Unknown strategy"):
            engine.mutate(sample_data, strategy="invalid_strategy_name")

    def test_update_effectiveness_new_strategy(self, engine):
        """Test effectiveness tracking for new strategy"""
        engine.update_effectiveness("new_strategy", found_coverage=False)

        stats = engine.get_stats()
        assert "new_strategy" in stats
        assert stats["new_strategy"]["attempts"] == 1
        assert stats["new_strategy"]["successes"] == 0

    def test_update_effectiveness_strategy_not_in_weights(self, engine):
        """Test updating effectiveness for strategy not in weights"""
        engine.update_effectiveness("unknown_strat", found_coverage=True)

        # Should still track it, just not adjust weights
        stats = engine.get_stats()
        assert "unknown_strat" in stats


class TestMutationConfig:
    """Test MutationConfig dataclass"""

    def test_default_config(self):
        """Test default configuration"""
        config = MutationConfig()

        assert config.deterministic_enabled is True
        assert config.havoc_enabled is True
        assert config.mutation_weights is not None
        assert "bit_flip" in config.mutation_weights

    def test_custom_config(self):
        """Test custom configuration"""
        config = MutationConfig(
            deterministic_enabled=False,
            havoc_iterations=500,
        )

        assert config.deterministic_enabled is False
        assert config.havoc_iterations == 500
