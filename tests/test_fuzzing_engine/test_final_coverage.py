"""Final edge case tests to achieve 99%+ coverage"""

import pytest
import tempfile
from pathlib import Path
from protocrash.fuzzing_engine.corpus import CorpusManager
from protocrash.monitors.memory_leak_detector import MemoryLeakDetector


class TestFinalCoverage:
    """Tests for final missing lines"""


    def test_corpus_missing_input_file(self):
        """Test CorpusManager when input file is missing (line 96)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus = CorpusManager(tmpdir)
            
            # Add input
            input_hash = corpus.add_input(b"test")
            
            # Delete the input file
            input_file = Path(tmpdir) / f"{input_hash}.input"
            input_file.unlink()
            
            # get_input should return None
            result = corpus.get_input(input_hash)
            assert result is None

    def test_memory_leak_less_than_10_snapshots(self):
        """Test MemoryLeakDetector with < 10 snapshots (line 117)"""
        detector = MemoryLeakDetector()
        
        # Add only 5 snapshots
        for i in range(5):
            detector.add_snapshot(i * 1.0, 1000 + i * 100, 2000)
        
        report = detector.detect_leak()
        
        # Should return LOW confidence
        assert report.confidence == "LOW"
        assert not report.leak_detected

    def test_memory_leak_low_growth_ratio(self):
        """Test MemoryLeakDetector with low growth ratio (line 130)"""
        detector = MemoryLeakDetector()
        
        # Add 20 snapshots with inconsistent growth
        for i in range(20):
            # Alternating growth and decrease
            rss = 1000 + (100 if i % 2 == 0 else -50)
            detector.add_snapshot(i * 1.0, rss, 2000)
        
        report = detector.detect_leak()
        
        # Should return LOW confidence due to inconsistent growth
        assert report.confidence == "LOW"
