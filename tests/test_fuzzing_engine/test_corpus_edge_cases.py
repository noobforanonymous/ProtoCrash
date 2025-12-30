"""Additional edge case tests for CorpusManager"""

import pytest
import tempfile
import json
from pathlib import Path
from protocrash.fuzzing_engine.corpus import CorpusManager


class TestCorpusManagerEdgeCases:
    """Test CorpusManager edge cases"""

    @pytest.fixture
    def corpus_dir(self):
        """Create temporary corpus directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def corpus(self, corpus_dir):
        """Create CorpusManager instance"""
        return CorpusManager(corpus_dir)

    def test_metadata_corrupt_handled_gracefully(self, corpus_dir):
        """Test corrupt metadata is handled gracefully"""
        # Create corpus with corrupt metadata
        metadata_file = Path(corpus_dir) / "metadata.json"
        metadata_file.write_text("{ corrupt json")
        
        # Should load without crashing
        corpus = CorpusManager(corpus_dir)
        assert corpus.get_size() == 0

    def test_metadata_empty_list(self, corpus_dir):
        """Test empty metadata list"""
        metadata_file = Path(corpus_dir) / "metadata.json"
        metadata_file.write_text("[]")
        
        corpus = CorpusManager(corpus_dir)
        assert corpus.get_size() == 0

    def test_add_input_with_all_metadata(self, corpus):
        """Test adding input with all metadata fields"""
        input_hash = corpus.add_input(
            b"test data",
            coverage_edges=100,
            found_new_coverage=True
        )
        
        metadata = corpus.get_metadata(input_hash)
        assert metadata is not None
        assert metadata.coverage_edges == 100
        assert metadata.found_new_coverage is True
        assert metadata.size == 9

    def test_increment_execution_count_nonexistent(self, corpus):
        """Test incrementing non-existent input does nothing"""
        # Should not crash
        corpus.increment_execution_count("nonexistent")
        
    def test_get_metadata_nonexistent(self, corpus):
        """Test getting metadata for nonexistent input"""
        result = corpus.get_metadata("nonexistent")
        assert result is None

    def test_export_stats_with_mixed_inputs(self, corpus):
        """Test export stats with various input types"""
        corpus.add_input(b"small", found_new_coverage=True)
        corpus.add_input(b"a" * 1000, found_new_coverage=False)
        corpus.add_input(b"medium" * 10, found_new_coverage=True)
        
        stats = corpus.export_stats()
        
        assert stats["corpus_size"] == 3
        assert stats["new_coverage_inputs"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["avg_input_size"] > 0

    def test_multiple_random_selections(self, corpus):
        """Test multiple random selections"""
        corpus.add_input(b"input1")
        corpus.add_input(b"input2")
        corpus.add_input(b"input3")
        
        # Get multiple random
        selections = set()
        for _ in range(20):
            selection = corpus.get_random_input()
            if selection:
                selections.add(selection)
        
        # Should have gotten different inputs
        assert len(selections) > 1
