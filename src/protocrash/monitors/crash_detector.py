"""Crash detection and analysis"""
import subprocess
import signal
from typing import List, Optional
from protocrash.core.types import CrashInfo, CrashType
class SignalHandler:
    """Handle Unix signals for crash detection"""
    # Signal to CrashType mapping
    SIGNAL_MAP = {
        signal.SIGSEGV: CrashType.SEGV,
        signal.SIGABRT: CrashType.ABRT,
        signal.SIGILL: CrashType.ILL,
        signal.SIGFPE: CrashType.FPE,
        signal.SIGBUS: CrashType.BUS,
    }
    @classmethod
    def classify_signal(cls, signal_num: int) -> Optional[CrashType]:
        """
        Classify signal number to crash type
        Args:
            signal_num: Signal number
        Returns:
            CrashType or None if not a crash signal
        """
        return cls.SIGNAL_MAP.get(signal_num)
    @classmethod
    def is_crash_signal(cls, signal_num: int) -> bool:
        """Check if signal indicates a crash"""
        return signal_num in cls.SIGNAL_MAP
class SanitizerMonitor:
    """Monitor sanitizer output for crashes"""
    ASAN_PATTERNS = [
        b"AddressSanitizer",
        b"heap-use-after-free",
        b"heap-buffer-overflow",
        b"stack-buffer-overflow",
        b"global-buffer-overflow",
        b"use-after-poison",
        b"use-after-scope",
    ]
    MSAN_PATTERNS = [
        b"MemorySanitizer",
        b"use-of-uninitialized-value",
    ]
    UBSAN_PATTERNS = [
        b"UndefinedBehaviorSanitizer",
        b"runtime error",
    ]
    @classmethod
    def detect_asan(cls, stderr: bytes) -> bool:
        """Detect AddressSanitizer crash"""
        return any(pattern in stderr for pattern in cls.ASAN_PATTERNS)
    @classmethod
    def detect_msan(cls, stderr: bytes) -> bool:
        """Detect MemorySanitizer crash"""
        return any(pattern in stderr for pattern in cls.MSAN_PATTERNS)
    @classmethod
    def detect_ubsan(cls, stderr: bytes) -> bool:
        """Detect UndefinedBehaviorSanitizer crash"""
        return any(pattern in stderr for pattern in cls.UBSAN_PATTERNS)
    @classmethod
    def extract_error_type(cls, stderr: bytes) -> str:
        """Extract sanitizer error type from stderr"""
        stderr_str = stderr.decode('utf-8', errors='ignore')
        # Look for error description after sanitizer name
        for line in stderr_str.split('\n'):
            if 'Sanitizer' in line or 'ERROR:' in line:
                return line.strip()
        return "Unknown sanitizer error"
class CrashDetector:
    """Main crash detection interface"""
    def __init__(self, timeout_ms: int = 5000):
        """
        Initialize crash detector
        Args:
            timeout_ms: Execution timeout in milliseconds
        """
        self.timeout_ms = timeout_ms
        self.signal_handler = SignalHandler()
        self.sanitizer_monitor = SanitizerMonitor()
    def execute_and_detect(
        self, target_cmd: List[str], input_data: bytes
    ) -> CrashInfo:
        """
        Execute target and detect crashes
        Args:
            target_cmd: Command to execute (e.g., ['./target', 'arg'])
            input_data: Input data to feed to stdin
        Returns:
            CrashInfo with crash details
        """
        try:
            proc = subprocess.Popen(
                target_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = proc.communicate(
                input=input_data,
                timeout=self.timeout_ms / 1000
            )
            exit_code = proc.returncode
            signal_num = None
            # Check if process was signaled
            if exit_code < 0:
                signal_num = -exit_code
            return self._analyze_execution(
                exit_code, signal_num, stdout, stderr, input_data
            )
        except subprocess.TimeoutExpired:
            # Timeout = hang
            proc.kill()
            proc.communicate()
            return CrashInfo(
                crashed=True,
                crash_type=CrashType.HANG,
                exit_code=-1,
                stderr=b"Execution timeout",
                input_data=input_data
            )
        except Exception as e:
            return CrashInfo(
                crashed=False,
                exit_code=-1,
                stderr=str(e).encode(),
                input_data=input_data
            )
    def _analyze_execution(
        self,
        exit_code: int,
        signal_num: Optional[int],
        stdout: bytes,
        stderr: bytes,
        input_data: bytes
    ) -> CrashInfo:
        """Analyze execution results for crashes"""
        # Check for sanitizer crashes first
        if self.sanitizer_monitor.detect_asan(stderr):
            return CrashInfo(
                crashed=True,
                crash_type=CrashType.ASAN,
                signal_number=signal_num,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                input_data=input_data
            )
        if self.sanitizer_monitor.detect_msan(stderr):
            return CrashInfo(
                crashed=True,
                crash_type=CrashType.MSAN,
                signal_number=signal_num,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                input_data=input_data
            )
        if self.sanitizer_monitor.detect_ubsan(stderr):
            return CrashInfo(
                crashed=True,
                crash_type=CrashType.UBSAN,
                signal_number=signal_num,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                input_data=input_data
            )
        # Check for signal-based crashes
        if signal_num and self.signal_handler.is_crash_signal(signal_num):
            crash_type = self.signal_handler.classify_signal(signal_num)
            return CrashInfo(
                crashed=True,
                crash_type=crash_type,
                signal_number=signal_num,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                input_data=input_data
            )
        # No crash detected
        return CrashInfo(
            crashed=False,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            input_data=input_data
        )
