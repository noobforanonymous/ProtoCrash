"""
Enhanced crash bucketing and deduplication
"""
import hashlib
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from protocrash.core.types import CrashInfo
from protocrash.monitors.stack_trace_parser import StackTrace, TraceParser
@dataclass
class CrashBucket:
    """Represents a group of similar crashes"""
    bucket_id: str
    crash_hash: str
    crash_type: str
    exploitability: str
    count: int = 0
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    sample_input: Optional[bytes] = None
    stack_trace: Optional[StackTrace] = None
    crashes: List[CrashInfo] = field(default_factory=list)
    def add_crash(self, crash: CrashInfo):
        """Add a crash to this bucket"""
        self.crashes.append(crash)
        self.count += 1
class CrashBucketing:
    """Enhanced crash bucketing with stack-based hashing"""
    def __init__(self, coarse_frames: int = 2, fine_frames: int = 5):
        """
        Initialize bucketing
        Args:
            coarse_frames: Number of frames for coarse bucketing
            fine_frames: Number of frames for fine-grained bucketing
        """
        self.coarse_frames = coarse_frames
        self.fine_frames = fine_frames
        self.buckets: Dict[str, CrashBucket] = {}
    def generate_stack_hash(self, trace: StackTrace, num_frames: int = 5) -> str:
        """
        Generate hash from top N stack frames
        Args:
            trace: Stack trace
            num_frames: Number of frames to include
        Returns:
            Hash string
        """
        if not trace or len(trace) == 0:
            return "empty_trace"
        components = []
        for frame in trace.get_top_frames(num_frames):
            # Include function name and address for uniqueness
            if frame.function:
                components.append(frame.function)
            if frame.address:
                components.append(frame.address[:8])  # First 8 chars of address
        if not components:
            return "no_symbols"
        combined = "|".join(components)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    def generate_coarse_hash(self, crash_info: CrashInfo) -> str:
        """
        Generate coarse-grained bucket hash
        Uses: crash type + top 2 frames
        Args:
            crash_info: Crash information
        Returns:
            Coarse hash
        """
        components = []
        # Crash type
        if crash_info.crash_type:
            components.append(crash_info.crash_type.value)
        # Parse stack trace if available
        if crash_info.stderr:
            trace = TraceParser.parse(crash_info.stderr)
            if len(trace) > 0:
                # Top 2 frames only
                for frame in trace.get_top_frames(self.coarse_frames):
                    if frame.function:
                        components.append(frame.function)
        if not components:
            return "unknown"
        combined = "|".join(components)
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    def generate_fine_hash(self, crash_info: CrashInfo) -> str:
        """
        Generate fine-grained bucket hash
        Uses: crash type + top 5 frames + addresses
        Args:
            crash_info: Crash information
        Returns:
            Fine hash
        """
        components = []
        # Crash type
        if crash_info.crash_type:
            components.append(crash_info.crash_type.value)
        # Signal number
        if crash_info.signal_number:
            components.append(f"sig{crash_info.signal_number}")
        # Parse stack trace
        if crash_info.stderr:
            trace = TraceParser.parse(crash_info.stderr)
            if len(trace) > 0:
                stack_hash = self.generate_stack_hash(trace, self.fine_frames)
                components.append(stack_hash)
        if not components:
            return "unknown"
        combined = "|".join(components)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    def compute_similarity(self, trace1: StackTrace, trace2: StackTrace) -> float:
        """
        Compute similarity score between two stack traces
        Args:
            trace1: First trace
            trace2: Second trace
        Returns:
            Similarity score (0.0 - 1.0)
        """
        if not trace1 or not trace2:
            return 0.0
        # Get function names from both traces
        funcs1 = set(f.function for f in trace1 if f.function)
        funcs2 = set(f.function for f in trace2 if f.function)
        if not funcs1 or not funcs2:
            return 0.0
        # Jaccard similarity
        intersection = len(funcs1 & funcs2)
        union = len(funcs1 | funcs2)
        if union == 0:
            return 0.0
        return intersection / union
    def bucket_crash(self, crash_info: CrashInfo) -> str:
        """
        Bucket a crash using fine-grained hash
        Args:
            crash_info: Crash to bucket
        Returns:
            Bucket ID
        """
        bucket_id = self.generate_fine_hash(crash_info)
        if bucket_id not in self.buckets:
            # Create new bucket
            trace = None
            if crash_info.stderr:
                trace = TraceParser.parse(crash_info.stderr)
            self.buckets[bucket_id] = CrashBucket(
                bucket_id=bucket_id,
                crash_hash=bucket_id,
                crash_type=crash_info.crash_type.value if crash_info.crash_type else "unknown",
                exploitability="unknown",
                sample_input=crash_info.input_data,
                stack_trace=trace
            )
        # Add crash to bucket
        self.buckets[bucket_id].add_crash(crash_info)
        return bucket_id
    def find_duplicates(self, crash_info: CrashInfo, similarity_threshold: float = 0.8) -> List[str]:
        """
        Find duplicate crashes based on similarity
        Args:
            crash_info: Crash to check
            similarity_threshold: Minimum similarity score
        Returns:
            List of bucket IDs of similar crashes
        """
        if not crash_info.stderr:
            return []
        trace = TraceParser.parse(crash_info.stderr)
        duplicates = []
        for bucket_id, bucket in self.buckets.items():
            if bucket.stack_trace:
                similarity = self.compute_similarity(trace, bucket.stack_trace)
                if similarity >= similarity_threshold:
                    duplicates.append(bucket_id)
        return duplicates
    def get_bucket_stats(self) -> Dict:
        """Get bucketing statistics"""
        return {
            'total_buckets': len(self.buckets),
            'total_crashes': sum(b.count for b in self.buckets.values()),
            'buckets_by_type': self._count_by_type(),
            'top_buckets': self._get_top_buckets(5)
        }
    def _count_by_type(self) -> Dict[str, int]:
        """Count buckets by crash type"""
        counts = {}
        for bucket in self.buckets.values():
            crash_type = bucket.crash_type
            counts[crash_type] = counts.get(crash_type, 0) + 1
        return counts
    def _get_top_buckets(self, n: int = 5) -> List[Dict]:
        """Get top N buckets by crash count"""
        sorted_buckets = sorted(
            self.buckets.values(),
            key=lambda b: b.count,
            reverse=True
        )
        return [{
            'bucket_id': b.bucket_id,
            'crash_type': b.crash_type,
            'count': b.count
        } for b in sorted_buckets[:n]]
