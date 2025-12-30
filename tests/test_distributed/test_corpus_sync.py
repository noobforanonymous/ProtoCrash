"""Comprehensive tests for CorpusSynchronizer"""

import pytest
import time
import tempfile
from pathlib import Path
from protocrash.distributed.corpus_sync import CorpusSynchronizer, SyncedInput


class TestCorpusSynchronizer:
    """Test CorpusSynchronizer class"""
    
    @pytest.fixture
    def temp_sync_dir(self):
        """Create temporary sync directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def synchronizer(self, temp_sync_dir):
        """Create CorpusSynchronizer instance"""
        return CorpusSynchronizer(temp_sync_dir, worker_id=0)
    
    def test_init(self, temp_sync_dir):
        """Test initialization creates directories"""
        sync = CorpusSynchronizer(temp_sync_dir, worker_id=5)
        
        assert sync.sync_dir == Path(temp_sync_dir)
        assert sync.worker_id == 5
        assert sync.last_sync_time == 0.0
        assert len(sync.exported_hashes) == 0
        
        # Check queue directory created
        queue_dir = Path(temp_sync_dir) / "worker_5" / "queue"
        assert queue_dir.exists()
        assert queue_dir.is_dir()
    
    def test_export_input(self, synchronizer):
        """Test exporting input to sync directory"""
        input_data = b"test input data"
        coverage_hash = "abc123def456"
        
        result = synchronizer.export_input(input_data, coverage_hash)
        
        assert result is True
        assert coverage_hash in synchronizer.exported_hashes
        
        # Verify file created
        files = list(synchronizer.queue_dir.iterdir())
        assert len(files) == 1
        
        # Verify content
        with open(files[0], 'rb') as f:
            assert f.read() == input_data
    
    def test_export_duplicate(self, synchronizer):
        """Test exporting duplicate input returns False"""
        input_data = b"duplicate test"
        coverage_hash = "duplicate_hash"
        
        # First export
        result1 = synchronizer.export_input(input_data, coverage_hash)
        assert result1 is True
        
        # Second export (duplicate)
        result2 = synchronizer.export_input(input_data, coverage_hash)
        assert result2 is False
        
        # Should still only have one file
        files = list(synchronizer.queue_dir.iterdir())
        assert len(files) == 1
    
    def test_export_multiple_inputs(self, synchronizer):
        """Test exporting multiple unique inputs"""
        inputs = [
            (b"input1", "hash1"),
            (b"input2", "hash2"),
            (b"input3", "hash3")
        ]
        
        for data, cov_hash in inputs:
            result = synchronizer.export_input(data, cov_hash)
            assert result is True
        
        # Verify all files created
        files = list(synchronizer.queue_dir.iterdir())
        assert len(files) == 3
    
    def test_import_new_inputs(self, temp_sync_dir):
        """Test importing inputs from other workers"""
        # Create worker 0 (this worker)
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        
        # Create worker 1 and export some inputs
        worker1 = CorpusSynchronizer(temp_sync_dir, worker_id=1)
        worker1.export_input(b"input from worker 1", "cov_hash_1")
        worker1.export_input(b"another input", "cov_hash_2")
        
        # Worker 0 imports from worker 1
        new_inputs = worker0.import_new_inputs()
        
        assert len(new_inputs) == 2
        assert all(isinstance(inp, SyncedInput) for inp in new_inputs)
        assert new_inputs[0].worker_id == 1
        assert new_inputs[0].input_data in [b"input from worker 1", b"another input"]
    
    def test_import_from_multiple_workers(self, temp_sync_dir):
        """Test importing from multiple workers"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        
        # Create workers 1, 2, 3 and export inputs
        worker1 = CorpusSynchronizer(temp_sync_dir, worker_id=1)
        worker1.export_input(b"from worker 1", "hash1")
        
        worker2 = CorpusSynchronizer(temp_sync_dir, worker_id=2)
        worker2.export_input(b"from worker 2", "hash2")
        
        worker3 = CorpusSynchronizer(temp_sync_dir, worker_id=3)
        worker3.export_input(b"from worker 3", "hash3")
        
        # Import all
        new_inputs = worker0.import_new_inputs()
        
        assert len(new_inputs) == 3
        worker_ids = {inp.worker_id for inp in new_inputs}
        assert worker_ids == {1, 2, 3}
    
    def test_import_respects_timestamp(self, temp_sync_dir):
        """Test timestamp-based import filtering"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        worker1 = CorpusSynchronizer(temp_sync_dir, worker_id=1)
        
        # Export first input
        worker1.export_input(b"old input", "hash_old")
        time.sleep(0.1)  # Small delay
        
        # Get current timestamp
        cutoff_time = time.time()
        time.sleep(0.1)
        
        # Export second input after cutoff
        worker1.export_input(b"new input", "hash_new")
        
        # Import only inputs after cutoff
        new_inputs = worker0.import_new_inputs(since_timestamp=cutoff_time)
        
        assert len(new_inputs) == 1
        assert new_inputs[0].input_data == b"new input"
    
    def test_import_skips_own_inputs(self, temp_sync_dir):
        """Test that worker doesn't import its own exports"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        
        # Export some inputs
        worker0.export_input(b"my input 1", "hash1")
        worker0.export_input(b"my input 2", "hash2")
        
        # Try to import (should get nothing)
        new_inputs = worker0.import_new_inputs()
        
        assert len(new_inputs) == 0
    
    def test_import_handles_corrupted_files(self, temp_sync_dir):
        """Test import skips corrupted files gracefully"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        worker1 = CorpusSynchronizer(temp_sync_dir, worker_id=1)
        
        # Export valid input
        worker1.export_input(b"valid input", "valid_hash")
        
        # Create corrupted file (wrong format)
        bad_file = worker1.queue_dir / "corrupted_file"
        bad_file.write_bytes(b"corrupted")
        
        # Import should skip corrupted file
        new_inputs = worker0.import_new_inputs()
        
        # Should only get the valid input
        assert len(new_inputs) == 1
        assert new_inputs[0].input_data == b"valid input"
    
    def test_import_updates_last_sync_time(self, temp_sync_dir):
        """Test that last_sync_time is updated after import"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        worker1 = CorpusSynchronizer(temp_sync_dir, worker_id=1)
        
        assert worker0.last_sync_time == 0.0
        
        worker1.export_input(b"test", "hash")
        
        time_before = time.time()
        worker0.import_new_inputs()
        time_after = time.time()
        
        assert time_before <= worker0.last_sync_time <= time_after
    
    def test_get_sync_stats(self, temp_sync_dir):
        """Test synchronization statistics"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        worker1 = CorpusSynchronizer(temp_sync_dir, worker_id=1)
        worker2 = CorpusSynchronizer(temp_sync_dir, worker_id=2)
        
        # Export inputs
        worker0.export_input(b"input0", "hash0")
        worker1.export_input(b"input1", "hash1")
        worker1.export_input(b"input1b", "hash1b")
        worker2.export_input(b"input2", "hash2")
        
        # Get stats from worker0
        stats = worker0.get_sync_stats()
        
        assert stats['total_workers'] == 3
        assert stats['total_synced_inputs'] == 4
        assert stats['exported_count'] == 1
        assert stats['last_sync_time'] == 0.0  # Haven't imported yet
    
    def test_cleanup(self, synchronizer):
        """Test cleanup removes queue files"""
        # Export some inputs
        synchronizer.export_input(b"input1", "hash1")
        synchronizer.export_input(b"input2", "hash2")
        
        # Verify files exist
        assert len(list(synchronizer.queue_dir.iterdir())) == 2
        
        # Cleanup
        synchronizer.cleanup()
        
        # Verify files removed
        assert len(list(synchronizer.queue_dir.iterdir())) == 0
    
    def test_filename_format(self, synchronizer):
        """Test exported filename format"""
        input_data = b"test data for filename"
        coverage_hash = "abcd1234efgh5678"
        
        synchronizer.export_input(input_data, coverage_hash)
        
        files = list(synchronizer.queue_dir.iterdir())
        assert len(files) == 1
        
        filename = files[0].name
        # Format: id_{input_hash}_{coverage_hash}
        assert filename.startswith("id_")
        assert "_abcd1234" in filename  # First 8 chars of coverage_hash
    
    def test_atomic_write_error_cleanup(self, synchronizer, monkeypatch):
        """Test that temp files are cleaned up on write error"""
        # Mock os.rename to raise an error
        import os
        original_rename = os.rename
        
        def mock_rename(src, dst):
            raise OSError("Mocked rename error")
        
        monkeypatch.setattr(os, 'rename', mock_rename)
        
        # Attempt export (should raise and clean up)
        with pytest.raises(OSError):
            synchronizer.export_input(b"test", "hash")
        
        # Verify no .tmp files left behind
        tmp_files = list(synchronizer.queue_dir.glob("*.tmp"))
        assert len(tmp_files) == 0
    
    def test_import_with_none_timestamp_uses_last_sync(self, temp_sync_dir):
        """Test that import with None timestamp uses last_sync_time"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        worker1 = CorpusSynchronizer(temp_sync_dir, worker_id=1)
        
        # Export first batch
        worker1.export_input(b"batch1", "hash1")
        
        # Import first batch
        batch1 = worker0.import_new_inputs()
        assert len(batch1) == 1
        
        # Export second batch
        time.sleep(0.1)
        worker1.export_input(b"batch2", "hash2")
        
        # Import with None (should use last_sync_time)
        batch2 = worker0.import_new_inputs(since_timestamp=None)
        assert len(batch2) == 1
        assert batch2[0].input_data == b"batch2"
    
    def test_synced_input_dataclass(self):
        """Test SyncedInput dataclass"""
        synced = SyncedInput(
            input_data=b"test",
            coverage_hash="abc123",
            timestamp=123.456,
            worker_id=5
        )
        
        assert synced.input_data == b"test"
        assert synced.coverage_hash == "abc123"
        assert synced.timestamp == 123.456
        assert synced.worker_id == 5
    
    def test_import_handles_non_worker_directories(self, temp_sync_dir):
        """Test import skips non-worker directories"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        
        # Create non-worker directory
        other_dir = Path(temp_sync_dir) / "other_stuff"
        other_dir.mkdir()
        (other_dir / "file.txt").write_text("not a worker dir")
        
        # Should not crash
        new_inputs = worker0.import_new_inputs()
        assert len(new_inputs) == 0
    
    def test_import_handles_invalid_worker_id(self, temp_sync_dir):
        """Test import handles invalid worker ID in directory name"""
        worker0 = CorpusSynchronizer(temp_sync_dir, worker_id=0)
        
        # Create directory with invalid worker ID
        invalid_dir = Path(temp_sync_dir) / "worker_invalid"
        invalid_dir.mkdir()
        queue_dir = invalid_dir / "queue"
        queue_dir.mkdir()
        (queue_dir / "test_file").write_bytes(b"test")
        
        # Should skip invalid directory
        new_inputs = worker0.import_new_inputs()
        assert len(new_inputs) == 0
    
    def test_export_creates_parent_directories(self, temp_sync_dir):
        """Test export creates parent directories if they don't exist"""
        # Remove queue directory to test creation
        sync_dir_path = Path(temp_sync_dir)
        worker_dir = sync_dir_path / "worker_99" / "queue"
        
        # Create synchronizer (will create directories)
        sync = CorpusSynchronizer(temp_sync_dir, worker_id=99)
        
        # Verify directory exists now
        assert worker_dir.exists()
        
        # Export should work
        result = sync.export_input(b"test", "hash")
        assert result is True
