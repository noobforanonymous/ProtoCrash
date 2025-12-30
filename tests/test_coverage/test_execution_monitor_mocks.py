"""Comprehensive ExecutionMonitor tests using mocking for edge cases"""

import pytest
import psutil
import subprocess
import time
from unittest.mock import Mock, PropertyMock, patch, MagicMock
from protocrash.monitors.execution_monitor import ExecutionMonitor, ExecutionStats


class TestExecutionMonitorExceptionHandling:
    """Test ExceptionMonitor exception handling paths using mocking"""

    def test_nosuchprocess_during_monitoring_loop(self):
        """Test NoSuchProcess exception during monitoring loop (lines 66-67)"""
        monitor = ExecutionMonitor(timeout_ms=5000)
        
        # Create a mock process that raises NoSuchProcess during monitoring
        mock_proc = Mock(spec=psutil.Process)
        mock_proc.is_running.side_effect = [True, True, psutil.NoSuchProcess(pid=123)]
        mock_proc.memory_info.side_effect = psutil.NoSuchProcess(pid=123)
        
        # Should handle gracefully and break out of loop
        stats = monitor.monitor_process(mock_proc)
        
        assert isinstance(stats, ExecutionStats)
        assert stats.exit_code == -1

    def test_accessdenied_during_monitoring_loop(self):
        """Test AccessDenied exception during monitoring loop (lines 66-67)"""
        monitor = ExecutionMonitor(timeout_ms=5000)
        
        # Create a mock process that raises AccessDenied
        mock_proc = Mock(spec=psutil.Process)
        # Loop check (True), exception breaks loop, timeout check (False), final check (False)
        mock_proc.is_running.side_effect = [True, False, False]
        mock_proc.memory_info.side_effect = psutil.AccessDenied(pid=123)
        mock_proc.wait.return_value = 0
        
        # Should handle gracefully and break
        stats = monitor.monitor_process(mock_proc)
        
        assert isinstance(stats, ExecutionStats)


    def test_timeoutexpired_during_wait(self):
        """Test TimeoutExpired exception during wait (lines 78-83)"""
        monitor = ExecutionMonitor(timeout_ms=100)
        
        # Create process that times out during wait
        mock_proc = Mock(spec=psutil.Process)
        # Loop check (False), timeout check (False), final check (False)
        mock_proc.is_running.side_effect = [False, False, False]
        mock_proc.wait.side_effect = psutil.TimeoutExpired(seconds=1)  # Always timeout
        mock_proc.kill = Mock()
        mock_proc.memory_info.return_value = Mock(rss=1000, vms=2000)
        mock_proc.io_counters.return_value = Mock(read_bytes=0, write_bytes=0)
        
        stats = monitor.monitor_process(mock_proc)
        
        # Should set exit_code to -1 and timed_out to True
        assert stats.exit_code == -1
        assert stats.timed_out is True
        mock_proc.kill.assert_called()

    def test_nosuchprocess_during_final_stats_collection(self):
        """Test NoSuchProcess during final stats collection (line 100-103)"""
        monitor = ExecutionMonitor(timeout_ms=5000)
        
        # Process that disappears during final stats collection
        mock_proc = Mock(spec=psutil.Process)
        # Loop check (False), timeout check (False), final check (False)
        mock_proc.is_running.side_effect = [False, False, False]
        # First wait succeeds, then memory_info raises exception
        mock_proc.wait.return_value = 0
        mock_proc.memory_info.side_effect = psutil.NoSuchProcess(pid=123)
        
        stats = monitor.monitor_process(mock_proc)
        
        # Should handle gracefully
        assert stats.exit_code == -1
        assert stats.memory_rss == 0
        assert stats.memory_vms == 0


    def test_accessdenied_during_final_stats_collection(self):
        """Test AccessDenied during final stats collection (line 100-103)"""
        monitor = ExecutionMonitor(timeout_ms=5000)
        
        mock_proc = Mock(spec=psutil.Process)
        mock_proc.is_running.side_effect = [False, False, False]
        mock_proc.wait.return_value = 0
        mock_proc.memory_info.side_effect = psutil.AccessDenied(pid=123)
        
        stats = monitor.monitor_process(mock_proc)
        
        # Should handle gracefully with default values
        assert stats.memory_rss == 0
        assert stats.memory_vms == 0
        assert stats.exit_code == -1


    def test_exception_during_exit_code_wait(self):
        """Test exception during wait for exit code (lines 93-94)"""
        monitor = ExecutionMonitor(timeout_ms=5000)
        
        mock_proc = Mock(spec=psutil.Process)
        mock_proc.is_running.side_effect = [False, False, False]  # Process finished
        mock_proc.wait.side_effect = [None, Exception("Random error")]  # First call ok, second fails
        mock_proc.memory_info.return_value = Mock(rss=1000, vms=2000)
        mock_proc.io_counters.return_value = Mock(read_bytes=0, write_bytes=0)
        
        stats = monitor.monitor_process(mock_proc)
        
        # Should catch exception and set exit_code to -1
        assert stats.exit_code == -1


    def test_process_still_running_after_timeout(self):
        """Test process still running after monitoring (lines 95-96)"""
        monitor = ExecutionMonitor(timeout_ms=100)
        
        # Use itertools.cycle for infinite True values
        from itertools import cycle
        mock_proc = Mock(spec=psutil.Process)
        # Process keeps running
        mock_proc.is_running.side_effect = cycle([True])
        mock_proc.memory_info.return_value = Mock(rss=1000, vms=2000)
        mock_proc.cpu_percent.return_value = 50.0
        mock_proc.kill = Mock()
        mock_proc.wait.return_value = -9  # Killed
        mock_proc.io_counters.return_value = Mock(read_bytes=0, write_bytes=0)
        
        stats = monitor.monitor_process(mock_proc)
        
        # Should set exit_code to -1 for still-running process
        assert stats.timed_out is True
        mock_proc.kill.assert_called()

    def test_missing_io_counters_attribute(self):
        """Test process without io_counters attribute (line 99)"""
        monitor = ExecutionMonitor(timeout_ms=5000)
        
        # Create mock without io_counters attribute
        mock_proc = Mock(spec=['is_running', 'wait', 'memory_info', 'cpu_percent'])
        mock_proc.is_running.side_effect = [False, False, False]  # Loop check, timeout check, final check
        mock_proc.wait.return_value = 0
        mock_proc.memory_info.return_value = Mock(rss=1000, vms=2000)
        
        stats = monitor.monitor_process(mock_proc)
        
        # Should use default 0 values for IO counters
        assert stats.io_read_bytes == 0
        assert stats.io_write_bytes == 0

    def test_io_counters_returns_none(self):
        """Test io_counters returning None"""
        monitor = ExecutionMonitor(timeout_ms=5000)
        
        mock_proc = Mock(spec=psutil.Process)
        mock_proc.is_running.side_effect = [False, False, False]  # Loop check, timeout check, final check
        mock_proc.wait.return_value = 0
        mock_proc.memory_info.return_value = Mock(rss=1000, vms=2000)
        mock_proc.io_counters.return_value = None
        
        stats = monitor.monitor_process(mock_proc)
        
        # Should handle None gracefully
        assert stats.io_read_bytes == 0
        assert stats.io_write_bytes == 0


    def test_complete_monitoring_cycle_with_samples(self):
        """Test complete monitoring with CPU and memory samples"""
        from itertools import cycle
        monitor = ExecutionMonitor(timeout_ms=500)
        
        mock_proc = Mock(spec=psutil.Process)
        # Process runs for a few sampling cycles then finishes
        is_running_calls = 0
        def is_running_side_effect():
            nonlocal is_running_calls
            is_running_calls += 1
            return is_running_calls < 4  # True for first 3 calls, False after
        
        mock_proc.is_running.side_effect = is_running_side_effect
        mock_proc.memory_info.return_value = Mock(rss=5000000, vms=10000000)
        mock_proc.cpu_percent.return_value = 75.5
        mock_proc.wait.return_value = 0
        mock_proc.io_counters.return_value = Mock(read_bytes=1024, write_bytes=2048)
        
        stats = monitor.monitor_process(mock_proc)
        
        # Should have collected samples
        assert stats.cpu_percent > 0
        assert stats.peak_memory > 0
        assert stats.execution_time > 0
        assert stats.exit_code == 0
        assert stats.timed_out is False
        assert stats.io_read_bytes == 1024
        assert stats.io_write_bytes == 2048

