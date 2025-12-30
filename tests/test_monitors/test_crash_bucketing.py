"""
Tests for crash bucketing
"""

import pytest
from protocrash.core.types import CrashInfo, CrashType
from protocrash.monitors.crash_bucketing import CrashBucketing, CrashBucket
from protocrash.monitors.stack_trace_parser import StackTrace, StackFrame


class TestCrashBucketing:
    """Test crash bucketing functionality"""
    
    def test_generate_stack_hash(self):
        """Test stack hash generation"""
        bucketing = CrashBucketing()
        
        trace = StackTrace()
        trace.add_frame(StackFrame(0, "deadbeef", "main"))
        trace.add_frame(StackFrame(1, "cafebabe", "foo"))
        
        hash1 = bucketing.generate_stack_hash(trace)
        assert isinstance(hash1, str)
        assert len(hash1) == 16
        
        # Same trace should give same hash
        hash2 = bucketing.generate_stack_hash(trace)
        assert hash1 == hash2
    
    def test_coarse_vs_fine_hash(self):
        """Test coarse and fine hashing produce different results"""
        bucketing = CrashBucketing(coarse_frames=2, fine_frames=5)
        
        crash = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            stderr=b"#0 0x123 in main\n#1 0x456 in foo\n#2 0x789 in bar"
        )
        
        coarse = bucketing.generate_coarse_hash(crash)
        fine = bucketing.generate_fine_hash(crash)
        
        assert coarse != fine
        assert len(coarse) == 12
        assert len(fine) == 16
    
    def test_bucket_crash(self):
        """Test crash bucketing"""
        bucketing = CrashBucketing()
        
        crash1 = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            stderr=b"#0 0x123 in main test.c:10"
        )
        
        bucket_id = bucketing.bucket_crash(crash1)
        assert bucket_id in bucketing.buckets
        assert bucketing.buckets[bucket_id].count >= 1
        
        # Same crash should go to same bucket
        crash2 = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            stderr=b"#0 0x123 in main test.c:10"
        )
        
        bucket_id2 = bucketing.bucket_crash(crash2)
        assert bucket_id == bucket_id2
        assert bucketing.buckets[bucket_id].count == 2
    
    def test_similarity_scoring(self):
        """Test stack trace similarity"""
        bucketing = CrashBucketing()
        
        # Identical traces
        trace1 = StackTrace()
        trace1.add_frame(StackFrame(0, "123", "main"))
        trace1.add_frame(StackFrame(1, "456", "foo"))
        
        trace2 = StackTrace()
        trace2.add_frame(StackFrame(0, "123", "main"))
        trace2.add_frame(StackFrame(1, "456", "foo"))
        
        similarity = bucketing.compute_similarity(trace1, trace2)
        assert similarity == 1.0
        
        # Partially similar
        trace3 = StackTrace()
        trace3.add_frame(StackFrame(0, "123", "main"))
        trace3.add_frame(StackFrame(1, "789", "bar"))
        
        similarity2 = bucketing.compute_similarity(trace1, trace3)
        assert 0.0 < similarity2 < 1.0
    
    def test_find_duplicates(self):
        """Test duplicate detection"""
        bucketing = CrashBucketing()
        
        # Add a crash to create a bucket
        crash1 = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            stderr=b"#0 0x123 in main\n#1 0x456 in foo"
        )
        bucketing.bucket_crash(crash1)
        
        # Similar crash
        crash2 = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            stderr=b"#0 0x789 in main\n#1 0xabc in foo"
        )
        
        duplicates = bucketing.find_duplicates(crash2, similarity_threshold=0.5)
        assert len(duplicates) > 0
    
    def test_bucket_stats(self):
        """Test bucketing statistics"""
        bucketing = CrashBucketing()
        
        for i in range(5):
            crash = CrashInfo(
                crashed=True,
                crash_type=CrashType.SEGV if i < 3 else CrashType.ABRT,
                stderr=f"#0 0x{i:03x} in func{i}".encode()
            )
            bucketing.bucket_crash(crash)
        
        stats = bucketing.get_bucket_stats()
        assert stats['total_buckets'] >= 2  # At least SEGV and ABRT
        assert stats['total_crashes'] >= 5  # Each crash may create own bucket
        assert 'buckets_by_type' in stats
        assert 'top_buckets' in stats
