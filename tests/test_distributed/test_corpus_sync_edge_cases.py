"""Additional edge case tests for CorpusSynchronizer to reach 95%+ coverage"""

import pytest
import time
import os
from pathlib import Path
from protocrash.distributed.corpus_sync import CorpusSynchronizer


class TestCorpusSyncEdgeCases:
    """Additional edge case tests for 95%+ coverage"""
    
    @pytest.fixture
    def temp_sync_dir(self, tmp_path):
        """Create temporary sync directory"""
        return str(tmp_path)
    
    def test_import_filters_old_files_exactly_at_timestamp(self, temp_sync_dir):
        """Test that files with mtime == since_timestamp are filtered"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        worker1 = CorpusSynchronizer(temp_sync_dir, worker_id=1)
        
        # Export input
        worker1.export_input(b"boundary test", "hash_boundary")
        
        # Get the exact mtime
        files = list(worker1.queue_dir.iterdir())
        exact_mtime = files[0].stat().st_mtime
        
        # Import with exact timestamp (should be filtered, <= not <)
        new_inputs = worker0.import_new_inputs(since_timestamp=exact_mtime)
        
        # File at exact timestamp should be filtered out
        assert len(new_inputs) == 0
    
    def test_import_with_missing_coverage_hash_in_filename(self, temp_sync_dir):
        """Test import handles filenames without coverage hash gracefully"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        worker1 = CorpusSynchronizer(temp_sync_dir, worker_id=1)
        
        # Create file with only 2 parts (missing coverage hash)
        bad_filename = worker1.queue_dir / "id_onlyinputhash"
        bad_filename.write_bytes(b"test data")
        
        # Should handle gracefully with empty coverage_hash
        new_inputs = worker0.import_new_inputs()
        
        # Should be skipped due to len(parts) < 3 check
        assert len(new_inputs) == 0
    
    def test_import_with_extra_underscores_in_filename(self, temp_sync_dir):
        """Test import handles filenames with extra underscores"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        worker1 = CorpusSynchronizer(temp_sync_dir, worker_id=1)
        
        # Create file with extra underscores: id_hash1_hash2_hash3
        filename = worker1.queue_dir / "id_inputhash_covhash1_extra"
        filename.write_bytes(b"extra underscore test")
        
        # Should take parts[2] as coverage_hash
        new_inputs = worker0.import_new_inputs()
        
        assert len(new_inputs) == 1
        assert new_inputs[0].coverage_hash == "covhash1"
    
    def test_cleanup_handles_file_deletion_errors(self, temp_sync_dir, monkeypatch):
        """Test cleanup continues even if file deletion fails"""
        sync = CorpusSynchronizer(temp_sync_dir, worker_id=10)
        
        # Export multiple files
        sync.export_input(b"file1", "hash1")
        sync.export_input(b"file2", "hash2")
        sync.export_input(b"file3", "hash3")
        
        # Mock unlink to fail on second file
        original_unlink = Path.unlink
        unlink_attempts = [0]
        
        def mock_unlink(self, *args, **kwargs):
            unlink_attempts[0] += 1
            if unlink_attempts[0] == 2:
                raise PermissionError("Mocked permission error")
            return original_unlink(self, *args, **kwargs)
        
        monkeypatch.setattr(Path, 'unlink', mock_unlink)
        
        # Cleanup should not crash
        sync.cleanup()
        
        # At least one file should be deleted
        remaining = list(sync.queue_dir.iterdir())
        assert len(remaining) < 3  # Not all files remain
    
    def test_export_with_very_long_coverage_hash(self, temp_sync_dir):
        """Test export handles very long coverage hashes"""
        sync = CorpusSynchronizer(temp_sync_dir, worker_id=15)
        
        # Very long coverage hash (>100 chars)
        long_hash = "a" * 150
        
        result = sync.export_input(b"long hash test", long_hash)
        
        assert result is True
        assert long_hash in sync.exported_hashes
        
        # Filename should still be created (uses first 8 chars)
        files = list(sync.queue_dir.iterdir())
        assert len(files) == 1
        assert "aaaaaaaa" in files[0].name  # First 8 chars
    
    def test_import_non_file_in_queue_directory(self, temp_sync_dir):
        """Test import skips non-file items (subdirectories)"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        worker1 = CorpusSynchronizer(temp_sync_dir, worker_id=1)
        
        # Create a subdirectory in queue
        subdir = worker1.queue_dir / "subdir"
        subdir.mkdir()
        
        # Also add valid file
        worker1.export_input(b"valid", "valid_hash")
        
        # Import should skip subdirectory
        new_inputs = worker0.import_new_inputs()
        
        # Should only get the valid file
        assert len(new_inputs) == 1
        assert new_inputs[0].input_data == b"valid"
    
    def test_get_sync_stats_with_non_worker_subdirs(self, temp_sync_dir):
        """Test get_sync_stats skips non-worker directories"""
        sync = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        
        # Create non-worker subdirectories
        other_dir1 = Path(temp_sync_dir) / "stats"
        other_dir1.mkdir()
        
        other_dir2 = Path(temp_sync_dir) / "metadata"
        other_dir2.mkdir()
        
        # Export one input
        sync.export_input(b"test", "hash")
        
        stats = sync.get_sync_stats()
        
        # Should only count worker directories
        assert stats['total_workers'] == 1  # Only worker_0
        assert stats['total_synced_inputs'] == 1
    
    def test_import_file_read_error_skips_gracefully(self, temp_sync_dir, monkeypatch):
        """Test import handles file read errors gracefully"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        worker1 = CorpusSynchronizer(temp_sync_dir, worker_id=1)
        
        # Export valid inputs
        worker1.export_input(b"good1", "hash1")
        worker1.export_input(b"good2", "hash2")
        
        # Mock open to raise on second file
        original_open = open
        open_attempts = [0]
        
        def mock_open(file, mode='r', *args, **kwargs):
            if mode == 'rb' and 'id_' in str(file):
                open_attempts[0] += 1
                if open_attempts[0] == 2:
                    raise IOError("Mocked read error")
            return original_open(file, mode, *args, **kwargs)
        
        monkeypatch.setattr('builtins.open', mock_open)
        
        # Import should skip failed file
        new_inputs = worker0.import_new_inputs()
        
        # Should get at least one good file
        assert len(new_inputs) >= 1
        assert len(new_inputs) < 2  # One failed

    def test_import_missing_queue_directory(self, temp_sync_dir):
        """Test import handles missing queue directory gracefully"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        
        # Create worker 1 directory but NO queue subdirectory
        worker1_dir = Path(temp_sync_dir) / "worker_1"
        worker1_dir.mkdir()
        # Deliberately do NOT create queue/
        
        # Import should handle missing queue directory
        new_inputs = worker0.import_new_inputs()
        assert len(new_inputs) == 0

