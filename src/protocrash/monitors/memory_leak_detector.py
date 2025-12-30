"""Memory leak detection"""
from collections import deque
from dataclasses import dataclass
from typing import List
@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""
    timestamp: float
    rss_bytes: int
    vms_bytes: int
@dataclass
class LeakReport:
    """Memory leak detection report"""
    leak_detected: bool
    growth_rate: float  # bytes per second
    total_growth: int  # bytes
    snapshots_analyzed: int
    confidence: str  # "HIGH", "MEDIUM", "LOW"
class MemoryLeakDetector:
    """Detect memory leaks by tracking memory growth"""
    def __init__(self, window_size: int = 50, threshold_mb: float = 10.0):
        """
        Initialize leak detector
        Args:
            window_size: Number of snapshots to analyze
            threshold_mb: Memory growth threshold in MB to report leak
        """
        self.window_size = window_size
        self.threshold_bytes = threshold_mb * 1024 * 1024
        self.snapshots: deque = deque(maxlen=window_size)
    def add_snapshot(self, timestamp: float, rss_bytes: int, vms_bytes: int) -> None:
        """
        Add memory snapshot
        Args:
            timestamp: Timestamp of snapshot
            rss_bytes: Resident set size in bytes
            vms_bytes: Virtual memory size in bytes
        """
        snapshot = MemorySnapshot(
            timestamp=timestamp,
            rss_bytes=rss_bytes,
            vms_bytes=vms_bytes
        )
        self.snapshots.append(snapshot)
    def detect_leak(self) -> LeakReport:
        """
        Analyze snapshots for memory leaks
        Returns:
            LeakReport with leak detection results
        """
        if len(self.snapshots) < 10:
            return LeakReport(
                leak_detected=False,
                growth_rate=0.0,
                total_growth=0,
                snapshots_analyzed=len(self.snapshots),
                confidence="LOW"
            )
        # Calculate memory growth
        snapshots_list = list(self.snapshots)
        first = snapshots_list[0]
        last = snapshots_list[-1]
        time_delta = last.timestamp - first.timestamp
        if time_delta == 0:
            return LeakReport(
                leak_detected=False,
                growth_rate=0.0,
                total_growth=0,
                snapshots_analyzed=len(snapshots_list),
                confidence="LOW"
            )
        # RSS growth
        rss_growth = last.rss_bytes - first.rss_bytes
        growth_rate = rss_growth / time_delta
        # Check if growth exceeds threshold
        leak_detected = rss_growth > self.threshold_bytes
        # Calculate confidence based on trend consistency
        confidence = self._calculate_confidence(snapshots_list)
        return LeakReport(
            leak_detected=leak_detected,
            growth_rate=growth_rate,
            total_growth=rss_growth,
            snapshots_analyzed=len(snapshots_list),
            confidence=confidence
        )
    def _calculate_confidence(self, snapshots: List[MemorySnapshot]) -> str:
        """
        Calculate confidence in leak detection
        Args:
            snapshots: List of memory snapshots
        Returns:
            Confidence level: "HIGH", "MEDIUM", "LOW"
        """
        if len(snapshots) < 10:
            return "LOW"
        # Check if memory is consistently growing
        increasing_count = 0
        for i in range(1, len(snapshots)):
            if snapshots[i].rss_bytes > snapshots[i-1].rss_bytes:
                increasing_count += 1
        growth_ratio = increasing_count / (len(snapshots) - 1)
        if growth_ratio > 0.8:
            return "HIGH"
        elif growth_ratio > 0.6:
            return "MEDIUM"
        else:
            return "LOW"
    def reset(self) -> None:
        """Clear all snapshots"""
        self.snapshots.clear()
