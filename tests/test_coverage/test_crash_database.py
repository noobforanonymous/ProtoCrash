"""Comprehensive tests for CrashDatabase"""

import pytest
import tempfile
import json
from pathlib import Path
from protocrash.monitors.crash_database import CrashDatabase
from protocrash.monitors.crash_bucketing import CrashBucket
from protocrash.monitors.stack_trace_parser import StackTrace
from protocrash.core.types import CrashInfo, CrashType


class TestCrashDatabase:
    """Test CrashDatabase class"""

    @pytest.fixture
    def db_path(self, tmp_path):
        """Create temporary database path"""
        return str(tmp_path / "test_crashes.db")

    @pytest.fixture
    def crash_db(self, db_path):
        """Create CrashDatabase instance"""
        db = CrashDatabase(db_path)
        yield db
        db.close()

    @pytest.fixture
    def sample_bucket(self):
        """Create sample crash bucket"""
        stack_trace = StackTrace()
        stack_trace.frames = [
            {'function': 'main', 'file': 'test.c', 'line': 42}
        ]
        
        return CrashBucket(
            bucket_id="bucket_001",
            crash_hash="abc123def456",
            crash_type="SEGV",
            exploitability="HIGH",
            count=1,
            first_seen="2024-01-01T00:00:00",
            last_seen="2024-01-01T00:00:00",
            stack_trace=stack_trace
        )

    @pytest.fixture
    def sample_crash_info(self):
        """Create sample crash info"""
        return CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            signal_number=11,
            exit_code=-11,
            stderr=b"Segmentation fault",
            input_data=b"CRASH_INPUT_DATA"
        )

    def test_init(self, db_path):
        """Test database initialization"""
        db = CrashDatabase(db_path)
        assert db.db_path == db_path
        assert db.conn is not None
        db.close()

    def test_add_crash_new(self, crash_db, sample_bucket, sample_crash_info):
        """Test adding new crash"""
        crash_id = crash_db.add_crash(sample_bucket, sample_crash_info)
        
        assert crash_id > 0
        
        # Verify crash was added
        crash = crash_db.get_crash_by_hash(sample_bucket.crash_hash)
        assert crash is not None
        assert crash['crash_hash'] == sample_bucket.crash_hash
        assert crash['bucket_id'] == sample_bucket.bucket_id
        assert crash['crash_type'] == sample_bucket.crash_type
        assert crash['exploitability'] == sample_bucket.exploitability
        assert crash['count'] == 1

    def test_add_crash_duplicate(self, crash_db, sample_bucket, sample_crash_info):
        """Test adding duplicate crash increments count"""
        # Add crash twice
        crash_id1 = crash_db.add_crash(sample_bucket, sample_crash_info)
        crash_id2 = crash_db.add_crash(sample_bucket, sample_crash_info)
        
        # Should return same ID
        assert crash_id1 == crash_id2
        
        # Count should be incremented
        crash = crash_db.get_crash_by_hash(sample_bucket.crash_hash)
        assert crash['count'] == 2

    def test_add_crash_without_input_data(self, crash_db, sample_bucket):
        """Test adding crash without input data"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            signal_number=11,
            input_data=None
        )
        
        crash_id = crash_db.add_crash(sample_bucket, crash_info)
        assert crash_id > 0
        
        crash = crash_db.get_crash_by_hash(sample_bucket.crash_hash)
        assert crash['input_size'] == 0

    def test_add_crash_without_stderr(self, crash_db, sample_bucket):
        """Test adding crash without stderr"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.HANG,
            stderr=None,
            input_data=b"test"
        )
        
        crash_id = crash_db.add_crash(sample_bucket, crash_info)
        crash = crash_db.get_crash_by_hash(sample_bucket.crash_hash)
        assert crash['stderr'] is None

    def test_add_crash_without_stack_trace(self, crash_db, sample_crash_info):
        """Test adding crash without stack trace"""
        bucket = CrashBucket(
            bucket_id="bucket_002",
            crash_hash="xyz789",
            crash_type="HANG",
            exploitability="LOW",
            count=1,
            first_seen="2024-01-01T00:00:00",
            last_seen="2024-01-01T00:00:00",
            stack_trace=None
        )
        
        crash_id = crash_db.add_crash(bucket, sample_crash_info)
        crash = crash_db.get_crash_by_hash(bucket.crash_hash)
        assert crash['stack_trace'] is None

    def test_get_crash_by_hash_not_found(self, crash_db):
        """Test getting non-existent crash"""
        crash = crash_db.get_crash_by_hash("nonexistent")
        assert crash is None

    def test_get_crashes_by_bucket(self, crash_db, sample_crash_info):
        """Test getting crashes by bucket ID"""
        # Add multiple crashes to same bucket
        bucket1 = CrashBucket(
            bucket_id="bucket_shared",
            crash_hash="crash1",
            crash_type="SEGV",
            exploitability="HIGH",
            count=1,
            first_seen="2024-01-01T00:00:00",
            last_seen="2024-01-01T00:00:00",
            stack_trace=None
        )
        
        bucket2 = CrashBucket(
            bucket_id="bucket_shared",
            crash_hash="crash2",
            crash_type="SEGV",
            exploitability="MEDIUM",
            count=1,
            first_seen="2024-01-01T00:00:00",
            last_seen="2024-01-01T00:00:00",
            stack_trace=None
        )
        
        crash_db.add_crash(bucket1, sample_crash_info)
        crash_db.add_crash(bucket2, sample_crash_info)
        
        crashes = crash_db.get_crashes_by_bucket("bucket_shared")
        assert len(crashes) == 2

    def test_get_crashes_by_bucket_empty(self, crash_db):
        """Test getting crashes from empty bucket"""
        crashes = crash_db.get_crashes_by_bucket("nonexistent")
        assert len(crashes) == 0

    def test_get_top_crashes(self, crash_db, sample_crash_info):
        """Test getting top crashes by count"""
        # Add crashes with different counts
        buckets = []
        for i in range(5):
            bucket = CrashBucket(
                bucket_id=f"bucket_{i}",
                crash_hash=f"crash_{i}",
                crash_type="SEGV",
                exploitability="HIGH",
                count=1,
                first_seen="2024-01-01T00:00:00",
                last_seen="2024-01-01T00:00:00",
                stack_trace=None
            )
            buckets.append(bucket)
            
            # Add crash multiple times to increase count
            for _ in range(i + 1):
                crash_db.add_crash(bucket, sample_crash_info)
        
        # Get top 3
        top_crashes = crash_db.get_top_crashes(limit=3)
        
        assert len(top_crashes) == 3
        # Should be ordered by count descending
        assert top_crashes[0]['count'] >= top_crashes[1]['count']
        assert top_crashes[1]['count'] >= top_crashes[2]['count']

    def test_get_top_crashes_empty_db(self, crash_db):
        """Test getting top crashes from empty database"""
        top_crashes = crash_db.get_top_crashes(limit=10)
        assert len(top_crashes) == 0

    def test_get_statistics_empty(self, crash_db):
        """Test statistics on empty database"""
        stats = crash_db.get_statistics()
        
        assert stats['total_unique_crashes'] == 0
        assert stats['total_occurrences'] == 0
        assert stats['by_type'] == {}
        assert stats['by_exploitability'] == {}

    def test_get_statistics_with_crashes(self, crash_db, sample_crash_info):
        """Test statistics with multiple crashes"""
        # Add crashes of different types
        bucket_segv = CrashBucket(
            bucket_id="bucket_segv",
            crash_hash="crash_segv",
            crash_type="SEGV",
            exploitability="HIGH",
            count=1,
            first_seen="2024-01-01T00:00:00",
            last_seen="2024-01-01T00:00:00",
            stack_trace=None
        )
        
        bucket_hang = CrashBucket(
            bucket_id="bucket_hang",
            crash_hash="crash_hang",
            crash_type="HANG",
            exploitability="LOW",
            count=1,
            first_seen="2024-01-01T00:00:00",
            last_seen="2024-01-01T00:00:00",
            stack_trace=None
        )
        
        # Add SEGV crash 3 times
        for _ in range(3):
            crash_db.add_crash(bucket_segv, sample_crash_info)
        
        # Add HANG crash once
        crash_db.add_crash(bucket_hang, sample_crash_info)
        
        stats = crash_db.get_statistics()
        
        assert stats['total_unique_crashes'] == 2
        assert stats['total_occurrences'] == 4
        assert 'SEGV' in stats['by_type']
        assert stats['by_type']['SEGV']['unique'] == 1
        assert stats['by_type']['SEGV']['total'] == 3
        assert 'HIGH' in stats['by_exploitability']
        assert 'LOW' in stats['by_exploitability']

    def test_export_to_json(self, crash_db, sample_bucket, sample_crash_info, tmp_path):
        """Test exporting database to JSON"""
        # Add some crashes
        crash_db.add_crash(sample_bucket, sample_crash_info)
        
        export_path = tmp_path / "export.json"
        crash_db.export_to_json(str(export_path))
        
        assert export_path.exists()
        
        # Verify JSON content
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        assert 'exported_at' in data
        assert 'statistics' in data
        assert 'crashes' in data
        assert len(data['crashes']) == 1
        assert data['crashes'][0]['crash_hash'] == sample_bucket.crash_hash

    def test_context_manager(self, db_path, sample_bucket, sample_crash_info):
        """Test using database as context manager"""
        with CrashDatabase(db_path) as db:
            crash_id = db.add_crash(sample_bucket, sample_crash_info)
            assert crash_id > 0
        
        # Database should be closed after context
        # Try to open again to verify it was closed properly
        with CrashDatabase(db_path) as db:
            crash = db.get_crash_by_hash(sample_bucket.crash_hash)
            assert crash is not None

    def test_close(self, crash_db):
        """Test closing database connection"""
        crash_db.close()
        # Should handle multiple closes gracefully
        crash_db.close()

    def test_database_persistence(self, db_path, sample_bucket, sample_crash_info):
        """Test data persists across database instances"""
        # Add crash and close
        db1 = CrashDatabase(db_path)
        crash_id = db1.add_crash(sample_bucket, sample_crash_info)
        db1.close()
        
        # Reopen and verify data exists
        db2 = CrashDatabase(db_path)
        crash = db2.get_crash_by_hash(sample_bucket.crash_hash)
        assert crash is not None
        assert crash['id'] == crash_id
        db2.close()
