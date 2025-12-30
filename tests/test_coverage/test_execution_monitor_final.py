"""Final execution monitor tests for 99%+ coverage"""

import pytest
import psutil
import subprocess
from unittest.mock import Mock, patch
from protocrash.monitors.execution_monitor import ExecutionMonitor


class TestExecutionMonitorFinalCoverage:
    """Tests for execution monitor missing lines"""

    def test_nosuchprocess_or_accessdenied_during_wait(self):
        """Test NoSuchProcess/AccessDenied exception during wait (lines 82-83)"""
        monitor = ExecutionMonitor(timeout_ms=1000)
        
        # Create a process that will raise NoSuchProcess during wait
        proc = subprocess.Popen(["sleep", "0.01"])
        ps_proc = psutil.Process(proc.pid)
        
        # Wait for it to finish
        proc.wait()
        
        # Mock wait to raise NoSuchProcess
        original_wait = ps_proc.wait
        def mock_wait(timeout=None):
            raise psutil.NoSuchProcess(pid=proc.pid)
        
        ps_proc.wait = mock_wait
        
        # Should handle exception
        stats = monitor.monitor_process(ps_proc)
        
        assert stats.exit_code == -1

    def test_accessdenied_during_wait(self):
        """Test AccessDenied exception during wait (lines 82-83)"""
        monitor = ExecutionMonitor(timeout_ms=1000)
        
        mock_proc = Mock(spec=psutil.Process)
        # Loop exits immediately, then wait raises AccessDenied
        mock_proc.is_running.side_effect = [False, False, False]
        # First wait call (line 75) raises AccessDenied exception
        def raise_access_denied(timeout=None):
            raise psutil.AccessDenied(pid=123)
        mock_proc.wait.side_effect = raise_access_denied
        mock_proc.memory_info.return_value = Mock(rss=1000, vms=2000)
        mock_proc.io_counters.return_value = Mock(read_bytes=0, write_bytes=0)
        
        stats = monitor.monitor_process(mock_proc)
        
        # Should handle gracefully
        assert stats.exit_code == -1

