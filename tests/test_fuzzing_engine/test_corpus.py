"""Test corpus management"""

import pytest
import tempfile
from pathlib import Path
from protocrash.fuzzing_engine.corpus import CorpusManager, CorpusEntry


class TestCorpusManager:
    """Test CorpusManager class"""

    @pytest.fixture
    def corpus_dir(self):
        """Create temporary corpus directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def corpus(self, corpus_dir):
        """Create CorpusManager instance"""
        return CorpusManager(corpus_dir)

    def test_init(self, corpus):
        """Test initialization"""
        assert corpus.corpus_dir.exists()
        assert corpus.get_size() == 0

    def test_add_input(self, corpus):
        """Test adding input"""
        input_data = b"test input"
        input_hash = corpus.add_input(input_data)
        
        assert isinstance(input_hash, str)
        assert len(input_hash) == 16  # SHA256 truncated
        assert corpus.get_size() == 1

    def test_add_duplicate(self, corpus):
        """Test adding duplicate input"""
        input_data = b"test input"
        hash1 = corpus.add_input(input_data)
        hash2 = corpus.add_input(input_data)
        
        assert hash1 == hash2
        assert corpus.get_size() == 1  # No duplicate

    def test_get_input(self, corpus):
        """Test getting input by hash"""
        input_data = b"test input"
        input_hash = corpus.add_input(input_data)
        
        retrieved = corpus.get_input(input_hash)
        assert retrieved == input_data

    def test_get_nonexistent(self, corpus):
        """Test getting nonexistent input"""
        result = corpus.get_input("nonexistent")
        assert result is None

    def test_get_random_input(self, corpus):
        """Test getting random input"""
        # Empty corpus
        assert corpus.get_random_input() is None
        
        # Add inputs
        corpus.add_input(b"input1")
        corpus.add_input(b"input2")
        corpus.add_input(b"input3")
        
        # Get random
        random_input = corpus.get_random_input()
        assert random_input in [b"input1", b"input2", b"input3"]

    def test_get_all_hashes(self, corpus):
        """Test getting all hashes"""
        hash1 = corpus.add_input(b"input1")
        hash2 = corpus.add_input(b"input2")
        
        hashes = corpus.get_all_hashes()
        assert len(hashes) == 2
        assert hash1 in hashes
        assert hash2 in hashes

    def test_increment_execution_count(self, corpus):
        """Test incrementing execution count"""
        input_hash = corpus.add_input(b"test")
        
        metadata = corpus.get_metadata(input_hash)
        assert metadata.execution_count == 0
        
        corpus.increment_execution_count(input_hash)
        metadata = corpus.get_metadata(input_hash)
        assert metadata.execution_count == 1

    def test_metadata_persistence(self, corpus_dir):
        """Test metadata persistence across instances"""
        # Create corpus and add input
        corpus1 = CorpusManager(corpus_dir)
        input_hash = corpus1.add_input(b"test", coverage_edges=10, found_new_coverage=True)
        
        # Create new instance
        corpus2 = CorpusManager(corpus_dir)
        assert corpus2.get_size() == 1
        
        metadata = corpus2.get_metadata(input_hash)
        assert metadata is not None
        assert metadata.coverage_edges == 10
        assert metadata.found_new_coverage is True

    def test_export_stats(self, corpus):
        """Test exporting corpus statistics"""
        # Empty corpus
        stats = corpus.export_stats()
        assert stats["corpus_size"] == 0
        
        # Add inputs
        corpus.add_input(b"A" * 100)
        corpus.add_input(b"B" * 200, found_new_coverage=True)
        corpus.add_input(b"C" * 300)
        
        stats = corpus.export_stats()
        assert stats["corpus_size"] == 3
        assert stats["total_size_bytes"] == 600
        assert stats["avg_input_size"] == 200.0
        assert stats["new_coverage_inputs"] == 1
