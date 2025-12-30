"""
Corpus synchronization for distributed fuzzing
Provides file-based corpus exchange between workers using
atomic operations and lock-free synchronization.
"""
import os
import time
import hashlib
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
@dataclass
class SyncedInput:
    """Synchronized input with metadata"""
    input_data: bytes
    coverage_hash: str
    timestamp: float
    worker_id: int
class CorpusSynchronizer:
    """
    File-based corpus synchronization for distributed fuzzing
    Uses atomic file operations (write + rename) to provide
    lock-free synchronization across multiple worker processes.
    """
    def __init__(self, sync_dir: str, worker_id: int):
        """
        Initialize corpus synchronizer
        Args:
            sync_dir: Base synchronization directory
            worker_id: This worker's unique identifier
        """
        self.sync_dir = Path(sync_dir)
        self.worker_id = worker_id
        self.last_sync_time = 0.0
        # Create worker-specific queue directory
        self.queue_dir = self.sync_dir / f"worker_{worker_id}" / "queue"
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        # Track exported inputs to avoid duplicates
        self.exported_hashes = set()
    def export_input(self, input_data: bytes, coverage_hash: str) -> bool:
        """
        Export input to sync directory for other workers
        Args:
            input_data: Input bytes to export
            coverage_hash: Coverage hash for deduplication
        Returns:
            True if exported, False if duplicate
        """
        # Check if already exported
        if coverage_hash in self.exported_hashes:
            return False
        # Generate unique filename
        input_hash = hashlib.sha256(input_data).hexdigest()[:16]
        filename = f"id_{input_hash}_{coverage_hash[:8]}"
        filepath = self.queue_dir / filename
        # Atomic write: write to temp, then rename
        temp_path = filepath.with_suffix('.tmp')
        try:
            with open(temp_path, 'wb') as f:
                f.write(input_data)
            # Atomic rename
            os.rename(temp_path, filepath)
            # Track export
            self.exported_hashes.add(coverage_hash)
            return True
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise e
    def import_new_inputs(self, since_timestamp: Optional[float] = None) -> List[SyncedInput]:
        """
        Import new inputs from other workers
        Args:
            since_timestamp: Only import inputs newer than this timestamp
                           If None, uses last_sync_time
        Returns:
            List of new synced inputs
        """
        if since_timestamp is None:
            since_timestamp = self.last_sync_time
        new_inputs = []
        # Scan all worker directories except our own
        for worker_dir in self.sync_dir.iterdir():
            if not worker_dir.is_dir():
                continue
            # Extract worker ID from directory name
            if not worker_dir.name.startswith('worker_'):
                continue
            try:
                other_worker_id = int(worker_dir.name.split('_')[1])
            except (IndexError, ValueError):
                continue
            # Skip our own directory
            if other_worker_id == self.worker_id:
                continue
            # Scan queue directory
            queue_dir = worker_dir / "queue"
            if not queue_dir.exists():
                continue
            for input_file in queue_dir.iterdir():
                if not input_file.is_file():
                    continue
                # Check file modification time
                mtime = input_file.stat().st_mtime
                if mtime <= since_timestamp:
                    continue
                # Parse filename: id_{input_hash}_{coverage_hash}
                parts = input_file.stem.split('_')
                if len(parts) < 3 or parts[0] != 'id':
                    continue
                coverage_hash = parts[2] if len(parts) > 2 else ''
                # Read input data
                try:
                    with open(input_file, 'rb') as f:
                        input_data = f.read()
                    new_inputs.append(SyncedInput(
                        input_data=input_data,
                        coverage_hash=coverage_hash,
                        timestamp=mtime,
                        worker_id=other_worker_id
                    ))
                except Exception:
                    # Skip corrupted files
                    continue
        # Update last sync time
        self.last_sync_time = time.time()
        return new_inputs
    def get_sync_stats(self) -> dict:
        """
        Get synchronization statistics
        Returns:
            Dict with sync metrics
        """
        total_inputs = 0
        total_workers = 0
        for worker_dir in self.sync_dir.iterdir():
            if not worker_dir.is_dir() or not worker_dir.name.startswith('worker_'):
                continue
            total_workers += 1
            queue_dir = worker_dir / "queue"
            if queue_dir.exists():
                total_inputs += sum(1 for _ in queue_dir.iterdir())
        return {
            'total_workers': total_workers,
            'total_synced_inputs': total_inputs,
            'exported_count': len(self.exported_hashes),
            'last_sync_time': self.last_sync_time
        }
    def cleanup(self):
        """Clean up worker's queue directory"""
        if self.queue_dir.exists():
            for input_file in self.queue_dir.iterdir():
                try:
                    input_file.unlink()
                except Exception:
                    pass
