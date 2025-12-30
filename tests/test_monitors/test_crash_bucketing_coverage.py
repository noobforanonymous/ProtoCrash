"""
Enhanced tests for crash bucketing to boost coverage
"""

import pytest
from protocrash.core.types import CrashInfo, CrashType
from protocrash.monitors.crash_bucketing import CrashBucketing, CrashBucket
from protocrash.monitors.stack_trace_parser import StackTrace, StackFrame


class TestCrashBucketingEnhanced:
    """Additional tests for crash bucketing coverage"""
    
    def test_empty_trace_hash(self):
        """Test hash generation with empty trace"""
        bucketing = CrashBucketing()
        
        # Empty trace
        trace = StackTrace()
        hash1 = bucketing.generate_stack_hash(trace)
        assert hash1 == "empty_trace"
        
        # Trace with no functions
        trace2 = StackTrace()
        trace2.add_frame(StackFrame(0, "deadbeef", None))
        hash2 = bucketing.generate_stack_hash(trace2)
        assert isinstance(hash2, str) and len(hash2) > 0
    
    def test_coarse_hash_edge_cases(self):
        """Test coarse hash with edge cases"""
        bucketing = CrashBucketing()
        
        # No crash type
        crash1 = CrashInfo(crashed=True)
        hash1 = bucketing.generate_coarse_hash(crash1)
        assert hash1 == "unknown"
        
        # No stderr
        crash2 = CrashInfo(crashed=True, crash_type=CrashType.SEGV)
        hash2 = bucketing.generate_coarse_hash(crash2)
        assert len(hash2) == 12
    
    def test_fine_hash_with_signal(self):
        """Test fine hash includes signal number"""
        bucketing = CrashBucketing()
        
        crash = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            signal_number=11,
            stderr=b"#0 0x123 in main"
        )
        
        hash1 = bucketing.generate_fine_hash(crash)
        assert isinstance(hash1, str)
        assert len(hash1) == 16
    
    def test_similarity_empty_traces(self):
        """Test similarity with empty/None traces"""
        bucketing = CrashBucketing()
        
        # Both empty
        trace1 = StackTrace()
        trace2 = StackTrace()
        assert bucketing.compute_similarity(trace1, trace2) == 0.0
        
        # One None
        assert bucketing.compute_similarity(None, trace2) == 0.0
        assert bucketing.compute_similarity(trace1, None) == 0.0
    
    def test_similarity_no_functions(self):
        """Test similarity when frames have no functions"""
        bucketing = CrashBucketing()
        
        trace1 = StackTrace()
        trace1.add_frame(StackFrame(0, "123", None))
        
        trace2 = StackTrace()
        trace2.add_frame(StackFrame(0, "456", None))
        
        similarity = bucketing.compute_similarity(trace1, trace2)
        assert similarity == 0.0
    
    def test_find_duplicates_no_stderr(self):
        """Test duplicate detection with no stderr"""
        bucketing = CrashBucketing()
        
        crash = CrashInfo(crashed=True, crash_type=CrashType.SEGV)
        duplicates = bucketing.find_duplicates(crash)
        assert duplicates == []
    
    def test_bucket_crash_no_stderr(self):
        """Test bucketing crash without stderr"""
        bucketing = CrashBucketing()
        
        crash = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            input_data=b"test"
        )
        
        bucket_id = bucketing.bucket_crash(crash)
        assert bucket_id in bucketing.buckets
        assert bucketing.buckets[bucket_id].stack_trace is None
    
    def test_multiple_crash_types(self):
        """Test bucketing with multiple crash types"""
        bucketing = CrashBucketing()
        
        # Create crashes of different types
        types = [CrashType.SEGV, CrashType.ABRT, CrashType.ILL, CrashType.FPE, CrashType.BUS]
        
        for crash_type in types:
            crash = CrashInfo(
                crashed=True,
                crash_type=crash_type,
                stderr=f"#0 0x123 in {crash_type.value}".encode()
            )
            bucketing.bucket_crash(crash)
        
        stats = bucketing.get_bucket_stats()
        assert stats['total_buckets'] >= len(types)
        assert len(stats['buckets_by_type']) >= len(types)
    
    def test_top_buckets_ordering(self):
        """Test top buckets are ordered by count"""
        bucketing = CrashBucketing()
        
        # Create bucket with many crashes
        for i in range(10):
            crash = CrashInfo(
                crashed=True,
                crash_type=CrashType.SEGV,
                stderr=b"#0 0x123 in main"  # Same hash
            )
            bucketing.bucket_crash(crash)
        
        # Create bucket with fewer crashes
        for i in range(3):
            crash = CrashInfo(
                crashed=True,
                crash_type=CrashType.ABRT,
                stderr=b"#0 0x456 in foo"  # Different hash
            )
            bucketing.bucket_crash(crash)
        
        stats = bucketing.get_bucket_stats()
        top = stats['top_buckets']
        
        # First bucket should have most crashes
        assert top[0]['count'] >= top[1]['count']
    
    def test_crash_bucket_dataclass(self):
        """Test CrashBucket dataclass"""
        crash = CrashInfo(crashed=True, crash_type=CrashType.SEGV)
        
        bucket = CrashBucket(
            bucket_id="test123",
            crash_hash="hash123",
            crash_type="SEGV",
            exploitability="HIGH"
        )
        
        assert bucket.count == 0
        bucket.add_crash(crash)
        assert bucket.count == 1
        assert len(bucket.crashes) == 1
    
    def test_stack_hash_different_frames(self):
        """Test stack hash with varying frame counts"""
        bucketing = CrashBucketing()
        
        trace = StackTrace()
        for i in range(10):
            trace.add_frame(StackFrame(i, f"addr{i}", f"func{i}"))
        
        # Test with different frame counts
        hash2 = bucketing.generate_stack_hash(trace, num_frames=2)
        hash5 = bucketing.generate_stack_hash(trace, num_frames=5)
        hash10 = bucketing.generate_stack_hash(trace, num_frames=10)
        
        # Different frame counts should produce different hashes
        assert hash2 != hash5
        assert hash5 != hash10
