"""Test execution monitor and memory leak detector"""

import pytest
import time
import subprocess
import psutil
from protocrash.monitors.execution_monitor import ExecutionMonitor, ExecutionStats
from protocrash.monitors.memory_leak_detector import MemoryLeakDetector, LeakReport


class TestExecutionMonitor:
    """Test ExecutionMonitor class"""

    @pytest.fixture
    def monitor(self):
        return ExecutionMonitor(timeout_ms=2000)

    def test_init(self, monitor):
        """Test initialization"""
        assert monitor.timeout_ms == 2000

    def test_monitor_process_success(self, monitor):
        """Test monitoring successful process"""
        # Start a simple process
        proc = subprocess.Popen(["echo", "test"], stdout=subprocess.PIPE)
        ps_proc = psutil.Process(proc.pid)
        
        # Wait for it to finish
        proc.wait(timeout=1)
        
        stats = monitor.monitor_process(ps_proc)
        
        assert isinstance(stats, ExecutionStats)
        assert stats.execution_time >= 0
        # Process finished quickly, should not timeout
        assert stats.timed_out is False or stats.execution_time < 0.5

    def test_monitor_process_timeout(self, monitor):
        """Test process timeout"""
        # Process that sleeps longer than timeout
        proc = subprocess.Popen(["sleep", "10"])
        ps_proc = psutil.Process(proc.pid)
        
        stats = monitor.monitor_process(ps_proc)
        
        assert stats.timed_out is True
        assert stats.execution_time < 3.0  # Should timeout around 2s

    def test_get_system_stats(self, monitor):
        """Test system stats collection"""
        stats = monitor.get_system_stats()
        
        assert "cpu_percent" in stats
        assert "memory_percent" in stats
        assert "memory_available" in stats
        assert stats["cpu_percent"] >= 0
        assert 0 <= stats["memory_percent"] <= 100


class TestMemoryLeakDetector:
    """Test MemoryLeakDetector class"""

    @pytest.fixture
    def detector(self):
        return MemoryLeakDetector(window_size=50, threshold_mb=1.0)

    def test_init(self, detector):
        """Test initialization"""
        assert detector.window_size == 50
        assert detector.threshold_bytes == 1.0 * 1024 * 1024

    def test_add_snapshot(self, detector):
        """Test adding snapshots"""
        detector.add_snapshot(1.0, 1000000, 2000000)
        detector.add_snapshot(2.0, 1100000, 2100000)
        
        assert len(detector.snapshots) == 2

    def test_detect_leak_insufficient_data(self, detector):
        """Test leak detection with insufficient data"""
        detector.add_snapshot(1.0, 1000000, 2000000)
        
        report = detector.detect_leak()
        
        assert report.leak_detected is False
        assert report.confidence == "LOW"

    def test_detect_no_leak(self, detector):
        """Test no leak detection"""
        base_time = time.time()
        base_memory = 1000000
        
        # Add stable memory snapshots
        for i in range(20):
            detector.add_snapshot(base_time + i * 0.1, base_memory + i * 100, base_memory * 2)
        
        report = detector.detect_leak()
        
        assert report.leak_detected is False

    def test_detect_leak(self, detector):
        """Test leak detection"""
        base_time = time.time()
        base_memory = 1000000
        
        # Add growing memory snapshots (2MB growth)
        for i in range(20):
            detector.add_snapshot(
                base_time + i * 0.1,
                base_memory + i * 100000,  # 100KB per snapshot
                base_memory * 2
            )
        
        report = detector.detect_leak()
        
        assert report.leak_detected is True
        assert report.growth_rate > 0
        assert report.total_growth > 0

    def test_confidence_high(self, detector):
        """Test high confidence leak detection"""
        base_time = time.time()
        base_memory = 1000000
        
        # Consistent growth
        for i in range(20):
            detector.add_snapshot(
                base_time + i * 0.1,
                base_memory + i * 10000,
                base_memory * 2
            )
        
        report = detector.detect_leak()
        
        assert report.confidence in ["HIGH", "MEDIUM"]

    def test_confidence_low(self, detector):
        """Test low confidence with inconsistent data"""
        base_time = time.time()
        base_memory = 1000000
        
        # Inconsistent growth
        for i in range(20):
            memory = base_memory + (i % 2) * 5000  # Alternating
            detector.add_snapshot(base_time + i * 0.1, memory, base_memory * 2)
        
        report = detector.detect_leak()
        
        # Confidence should be low due to inconsistency
        assert report.confidence in ["LOW", "MEDIUM"]

    def test_reset(self, detector):
        """Test reset functionality"""
        detector.add_snapshot(1.0, 1000000, 2000000)
        detector.add_snapshot(2.0, 1100000, 2100000)
        
        assert len(detector.snapshots) == 2
        
        detector.reset()
        
        assert len(detector.snapshots) == 0

    def test_window_size_limit(self, detector):
        """Test window size limit"""
        base_time = time.time()
        
        # Add more than window size
        for i in range(100):
            detector.add_snapshot(base_time + i * 0.1, 1000000 + i * 1000, 2000000)
        
        # Should only keep window_size snapshots
        assert len(detector.snapshots) == detector.window_size

    def test_zero_time_delta(self, detector):
        """Test leak detection with zero time delta"""
        base_time = time.time()
        
        # All at same timestamp
        for i in range(15):
            detector.add_snapshot(base_time, 1000000 + i * 1000, 2000000)
        
        report = detector.detect_leak()
        
        # Should handle gracefully
        assert report.leak_detected is False
        assert report.growth_rate == 0.0

    def test_decreasing_memory(self, detector):
        """Test with decreasing memory usage"""
        base_time = time.time()
        base_memory = 2000000
        
        # Decreasing memory
        for i in range(20):
            detector.add_snapshot(
                base_time + i * 0.1,
                base_memory - i * 10000,
                base_memory * 2
            )
        
        report = detector.detect_leak()
        
        # Negative growth shouldn't be a leak
        assert report.leak_detected is False
        assert report.confidence == "LOW"


class TestExecutionMonitorAdvanced:
    """Advanced tests for ExecutionMonitor"""

    def test_monitor_with_io_counters(self):
        """Test monitoring process with IO"""
        monitor = ExecutionMonitor(timeout_ms=5000)
        
        # Process that does some IO
        proc = subprocess.Popen(["ls", "/"], stdout=subprocess.PIPE)
        ps_proc = psutil.Process(proc.pid)
        
        proc.wait(timeout=1)
        stats = monitor.monitor_process(ps_proc)
        
        assert isinstance(stats, ExecutionStats)

    def test_monitor_already_dead_process(self):
        """Test monitoring process that already finished"""
        monitor = ExecutionMonitor(timeout_ms=100)  # Short timeout
        
        # Very quick process
        proc = subprocess.Popen(["echo", "done"], stdout=subprocess.PIPE)
        proc.wait()  # Ensure it's done
        
        # Give it a moment to be reaped
        time.sleep(0.1)
        
        # Try to monitor - should handle gracefully
        try:
            ps_proc = psutil.Process(proc.pid)
            stats = monitor.monitor_process(ps_proc)
            assert isinstance(stats, ExecutionStats)
        except psutil.NoSuchProcess:
            # Expected - process already gone
            pass

    def test_monitor_cpu_sampling(self):
        """Test CPU sampling works"""
        monitor = ExecutionMonitor(timeout_ms=1000)
        
        # CPU-intensive process
        proc = subprocess.Popen(["python3", "-c", "sum(range(1000000))"])
        ps_proc = psutil.Process(proc.pid)
        
        stats = monitor.monitor_process(ps_proc)
        
        # Should have collected some CPU samples
        assert stats.execution_time > 0

    def test_peak_memory_tracking(self):
        """Test peak memory is tracked"""
        monitor = ExecutionMonitor(timeout_ms=5000)
        
        proc = subprocess.Popen(["python3", "-c", "x = [0] * 1000000"])
        ps_proc = psutil.Process(proc.pid)
        
        stats = monitor.monitor_process(ps_proc)
        
        # Peak memory should be recorded
        assert stats.peak_memory >= 0

    def test_monitor_process_access_denied(self):
        """Test handling AccessDenied exception"""
        monitor = ExecutionMonitor(timeout_ms=2000)
        
        # Start a process
        proc = subprocess.Popen(["sleep", "0.1"])
        ps_proc = psutil.Process(proc.pid)
        
        # Kill it immediately to trigger NoSuchProcess
        proc.kill()
        proc.wait()
        
        # Try to monitor dead process
        try:
            stats = monitor.monitor_process(ps_proc)
            # Should handle gracefully with exit_code -1
            assert stats.exit_code == -1
        except psutil.NoSuchProcess:
            # Also acceptable
            pass

    def test_monitor_timeout_exception(self):
        """Test TimeoutExpired during wait"""
        monitor = ExecutionMonitor(timeout_ms=100)
        
        # Very short timeout to trigger timeout
        proc = subprocess.Popen(["sleep", "10"])
        ps_proc = psutil.Process(proc.pid)
        
        stats = monitor.monitor_process(ps_proc)
        
        # Should timeout and kill process
        assert stats.timed_out is True

    def test_monitor_no_io_counters(self):
        """Test process without IO counters"""
        monitor = ExecutionMonitor(timeout_ms=5000)
        
        proc = subprocess.Popen(["echo", "test"], stdout=subprocess.PIPE)
        ps_proc = psutil.Process(proc.pid)
        proc.wait(timeout=1)
        
        stats = monitor.monitor_process(ps_proc)
        
        # Should handle missing io_counters gracefully
        assert stats.io_read_bytes >= 0
        assert stats.io_write_bytes >= 0


class TestMemoryLeakDetectorAdvanced:

    """Advanced tests for MemoryLeakDetector"""

    def test_medium_confidence(self):
        """Test medium confidence detection"""
        detector = MemoryLeakDetector(window_size=50, threshold_mb=0.1)
        base_time = time.time()
        base_memory = 1000000
        
        # 70% increasing (medium confidence)
        for i in range(20):
            if i % 10 < 7:  # 70% increasing
                memory = base_memory + i * 10000
            else:
                memory = base_memory + (i-1) * 10000
            detector.add_snapshot(base_time + i * 0.1, memory, base_memory * 2)
        
        report = detector.detect_leak()
        
        assert report.confidence in ["MEDIUM", "HIGH"]

    def test_exact_threshold(self):
        """Test memory growth exactly at threshold"""
        detector = MemoryLeakDetector(window_size=50, threshold_mb=1.0)
        base_time = time.time()
        base_memory = 1000000
        threshold_bytes = 1024 * 1024
        
        # Grow exactly threshold amount
        for i in range(20):
            detector.add_snapshot(
                base_time + i * 0.1,
                base_memory + (threshold_bytes // 19) * i,
                base_memory * 2
            )
        
        report = detector.detect_leak()
        
        # Should be close to threshold
        assert abs(report.total_growth - threshold_bytes) < 100000

