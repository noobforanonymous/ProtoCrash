"""Test coverage tracker"""

import pytest
from pathlib import Path
from protocrash.monitors.coverage import CoverageTracker


class TestCoverageTracker:
    """Test CoverageTracker class"""

    @pytest.fixture
    def tracker(self):
        return CoverageTracker()

    def test_init(self, tracker):
        """Test initialization"""
        assert tracker.coverage_map is not None
        assert tracker.comparator is not None
        assert tracker.analyzer is not None
        assert tracker.run_count == 0

    def test_start_run(self, tracker):
        """Test starting a run"""
        tracker.start_run()
        
        assert tracker.run_count == 1
        assert tracker.coverage_map.get_edge_count() == 0

    def test_end_run_with_coverage(self, tracker):
        """Test ending run with new coverage"""
        tracker.start_run()
        tracker.record_edge(0x1234)
        
        has_new = tracker.end_run()
        
        assert has_new is True
        assert len(tracker.coverage_history) == 1

    def test_end_run_without_coverage(self, tracker):
        """Test ending run without new coverage"""
        # First run with coverage
        tracker.start_run()
        tracker.record_edge(0x1234)
        tracker.end_run()
        
        # Second run with same coverage
        tracker.start_run()
        tracker.record_edge(0x1234)
        has_new = tracker.end_run()
        
        assert has_new is False
        assert len(tracker.coverage_history) == 1  # No new entry

    def test_record_edge(self, tracker):
        """Test recording edges"""
        tracker.start_run()
        tracker.record_edge(0x1234)
        tracker.record_edge(0x5678)
        
        bitmap = tracker.get_coverage_bitmap()
        assert any(b > 0 for b in bitmap)

    def test_get_coverage_bitmap(self, tracker):
        """Test getting coverage bitmap"""
        tracker.start_run()
        tracker.record_edge(0x1234)
        
        bitmap = tracker.get_coverage_bitmap()
        
        assert isinstance(bitmap, bytearray)
        assert len(bitmap) == 65536

    def test_get_stats(self, tracker):
        """Test getting coverage statistics"""
        tracker.start_run()
        tracker.record_edge(0x1234)
        tracker.record_edge(0x5678)
        
        stats = tracker.get_stats()
        
        assert stats.unique_edges > 0
        assert stats.edge_density > 0

    def test_get_total_edges(self, tracker):
        """Test getting total edges found"""
        assert tracker.get_total_edges() == 0
        
        tracker.start_run()
        tracker.record_edge(0x1234)
        tracker.end_run()
        
        assert tracker.get_total_edges() > 0

    def test_export_import_coverage(self, tracker, tmp_path):
        """Test exporting and importing coverage"""
        # Create coverage
        tracker.start_run()
        tracker.record_edge(0x1234)
        tracker.record_edge(0x5678)
        
        original_bitmap = tracker.get_coverage_bitmap()
        
        # Export
        export_file = tmp_path / "coverage.bin"
        tracker.export_coverage(export_file)
        
        assert export_file.exists()
        assert export_file.stat().st_size == 65536
        
        # Create new tracker and import
        new_tracker = CoverageTracker()
        new_tracker.import_coverage(export_file)
        
        imported_bitmap = new_tracker.get_coverage_bitmap()
        assert imported_bitmap == original_bitmap

    def test_import_invalid_file(self, tracker, tmp_path):
        """Test importing invalid coverage file"""
        invalid_file = tmp_path / "invalid.bin"
        invalid_file.write_bytes(b"INVALID" * 100)
        
        with pytest.raises(ValueError, match="Invalid coverage file size"):
            tracker.import_coverage(invalid_file)

    def test_multiple_runs(self, tracker):
        """Test multiple fuzzing runs"""
        # Run 1
        tracker.start_run()
        tracker.record_edge(0x1111)
        has_new1 = tracker.end_run()
        
        # Run 2 with new coverage
        tracker.start_run()
        tracker.record_edge(0x2222)
        has_new2 = tracker.end_run()
        
        # Run 3 with repeated coverage
        tracker.start_run()
        tracker.record_edge(0x1111)
        has_new3 = tracker.end_run()
        
        assert has_new1 is True
        assert has_new2 is True
        assert has_new3 is False
        assert tracker.run_count == 3
        assert len(tracker.coverage_history) == 2  # Only 2 unique
