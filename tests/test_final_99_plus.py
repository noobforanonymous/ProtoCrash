"""Final 2 tests for 99%+ coverage"""

import pytest
from protocrash.mutators.mutation_engine import MutationEngine, MutationConfig


class TestFinal99Plus:
    """Tests for the absolute final 2 missing lines"""

    def test_version_import(self):
        """Test __version__.py line 3: __version__ = "0.1.0" """
        # Direct import covers the line
        import protocrash.core.types  # Force package load
        import protocrash.__version__ as version_module
        
        assert version_module.__version__ == "0.1.0"

    def test_mutation_config_none_weights(self):
        """Test mutation_engine.py line 31: if self.mutation_weights is None (True branch)"""
        config = MutationConfig()
        assert config.mutation_weights is not None
        assert "bit_flip" in config.mutation_weights

    def test_mutation_config_with_weights(self):
        """Test mutation_engine.py line 31: if self.mutation_weights is None (False branch)"""
        weights = {"custom": 1.0}
        config = MutationConfig(mutation_weights=weights)
        # Should NOT overwrite custom weights
        assert config.mutation_weights == weights
        assert "bit_flip" not in config.mutation_weights


