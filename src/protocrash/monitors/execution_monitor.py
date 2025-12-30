"""Execution monitoring and resource tracking"""
import psutil
import time
from dataclasses import dataclass
@dataclass
class ExecutionStats:
    """Statistics from execution monitoring"""
    execution_time: float  # seconds
    cpu_percent: float
    memory_rss: int  # bytes
    memory_vms: int  # bytes
    peak_memory: int  # bytes
    io_read_bytes: int
    io_write_bytes: int
    exit_code: int
    timed_out: bool
class ExecutionMonitor:
    """Monitor process execution and resource usage"""
    def __init__(self, timeout_ms: int = 5000):
        """
        Initialize execution monitor
        Args:
            timeout_ms: Execution timeout in milliseconds
        """
        self.timeout_ms = timeout_ms
    def monitor_process(self, proc: psutil.Process) -> ExecutionStats:
        """
        Monitor a running process
        Args:
            proc: psutil.Process to monitor
        Returns:
            ExecutionStats with resource usage
        """
        start_time = time.time()
        peak_memory = 0
        cpu_samples = []
        timed_out = False
        try:
            # Monitor while running
            timeout_seconds = self.timeout_ms / 1000
            while proc.is_running() and (time.time() - start_time) < timeout_seconds:
                try:
                    # Get memory info
                    mem_info = proc.memory_info()
                    peak_memory = max(peak_memory, mem_info.rss)
                    # Get CPU percent
                    cpu_percent = proc.cpu_percent(interval=0.1)
                    cpu_samples.append(cpu_percent)
                    time.sleep(0.05)  # Sample every 50ms
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
            # Check if timed out
            if proc.is_running():
                proc.kill()
                timed_out = True
            # Wait for process to finish
            proc.wait(timeout=1)
        except psutil.TimeoutExpired:
            proc.kill()
            timed_out = True
            exit_code = -1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            exit_code = -1
        # Collect final stats
        execution_time = time.time() - start_time
        try:
            # Get exit code if process finished
            if not proc.is_running():
                try:
                    exit_code = proc.wait(timeout=0.1)
                except:
                    exit_code = -1
            else:
                exit_code = -1
            mem_info = proc.memory_info()
            io_counters = proc.io_counters() if hasattr(proc, 'io_counters') else None
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            mem_info = None
            io_counters = None
            exit_code = -1
        return ExecutionStats(
            execution_time=execution_time,
            cpu_percent=sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0,
            memory_rss=mem_info.rss if mem_info else 0,
            memory_vms=mem_info.vms if mem_info else 0,
            peak_memory=peak_memory,
            io_read_bytes=io_counters.read_bytes if io_counters else 0,
            io_write_bytes=io_counters.write_bytes if io_counters else 0,
            exit_code=exit_code,
            timed_out=timed_out
        )
    def get_system_stats(self) -> dict:
        """
        Get current system resource usage
        Returns:
            Dictionary with system stats
        """
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage_percent": psutil.disk_usage('/').percent,
        }
