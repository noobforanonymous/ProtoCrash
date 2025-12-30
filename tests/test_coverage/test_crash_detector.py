"""Test crash detector"""

import pytest
import signal
import subprocess
from protocrash.monitors.crash_detector import CrashDetector, SignalHandler, SanitizerMonitor
from protocrash.core.types import CrashType


class TestSignalHandler:
    """Test SignalHandler class"""

    def test_classify_signal_segv(self):
        """Test SIGSEGV classification"""
        crash_type = SignalHandler.classify_signal(signal.SIGSEGV)
        assert crash_type == CrashType.SEGV

    def test_classify_signal_abrt(self):
        """Test SIGABRT classification"""
        crash_type = SignalHandler.classify_signal(signal.SIGABRT)
        assert crash_type == CrashType.ABRT

    def test_classify_signal_unknown(self):
        """Test unknown signal"""
        crash_type = SignalHandler.classify_signal(999)
        assert crash_type is None

    def test_is_crash_signal(self):
        """Test crash signal detection"""
        assert SignalHandler.is_crash_signal(signal.SIGSEGV) is True
        assert SignalHandler.is_crash_signal(signal.SIGTERM) is False


class TestSanitizerMonitor:
    """Test SanitizerMonitor class"""

    def test_detect_asan(self):
        """Test ASan detection"""
        stderr = b"AddressSanitizer: heap-use-after-free on address 0x..."
        assert SanitizerMonitor.detect_asan(stderr) is True

    def test_detect_asan_negative(self):
        """Test ASan negative"""
        stderr = b"Normal output"
        assert SanitizerMonitor.detect_asan(stderr) is False

    def test_detect_msan(self):
        """Test MSan detection"""
        stderr = b"MemorySanitizer: use-of-uninitialized-value"
        assert SanitizerMonitor.detect_msan(stderr) is True

    def test_detect_ubsan(self):
        """Test UBSan detection"""
        stderr = b"UndefinedBehaviorSanitizer: runtime error: division by zero"
        assert SanitizerMonitor.detect_ubsan(stderr) is True

    def test_extract_error_type(self):
        """Test error type extraction"""
        stderr = b"AddressSanitizer: heap-buffer-overflow\nDetails..."
        error = SanitizerMonitor.extract_error_type(stderr)
        assert "AddressSanitizer" in error


class TestCrashDetector:
    """Test CrashDetector class"""

    @pytest.fixture
    def detector(self):
        return CrashDetector(timeout_ms=1000)

    def test_init(self, detector):
        """Test initialization"""
        assert detector.timeout_ms == 1000
        assert detector.signal_handler is not None
        assert detector.sanitizer_monitor is not None

    def test_execute_success(self, detector):
        """Test successful execution (no crash)"""
        crash_info = detector.execute_and_detect(
            ["echo", "test"],
            b"input"
        )

        assert crash_info.crashed is False
        assert crash_info.exit_code == 0

    def test_execute_timeout(self, detector):
        """Test execution timeout"""
        # Sleep for longer than timeout
        crash_info = detector.execute_and_detect(
            ["sleep", "10"],
            b""
        )

        assert crash_info.crashed is True
        assert crash_info.crash_type == CrashType.HANG

    def test_execute_nonexistent_command(self, detector):
        """Test nonexistent command"""
        crash_info = detector.execute_and_detect(
            ["nonexistent_command_12345"],
            b""
        )

        # Should handle gracefully
        assert crash_info.crashed is False

    def test_detect_asan_crash(self, detector):
        """Test ASan crash detection"""
        # Simulate ASan output
        class MockPopen:
            returncode = -signal.SIGABRT
            
            def __init__(self, *args, **kwargs):
                pass
            
            def communicate(self, *args, **kwargs):
                stderr = b"AddressSanitizer: heap-use-after-free"
                return b"", stderr
        
        # Monkeypatch subprocess.Popen
        import protocrash.monitors.crash_detector as cd_module
        original_popen = cd_module.subprocess.Popen
        cd_module.subprocess.Popen = MockPopen
        
        crash_info = detector.execute_and_detect(["dummy"], b"test")
        
        # Restore
        cd_module.subprocess.Popen = original_popen
        
        assert crash_info.crashed is True
        assert crash_info.crash_type == CrashType.ASAN

    def test_analyze_msan_crash(self, detector):
        """Test MSan crash analysis"""
        crash_info = detector._analyze_execution(
            exit_code=1,
            signal_num=None,
            stdout=b"",
            stderr=b"MemorySanitizer: use-of-uninitialized-value",
            input_data=b"test"
        )
        
        assert crash_info.crashed is True
        assert crash_info.crash_type == CrashType.MSAN

    def test_analyze_ubsan_crash(self, detector):
        """Test UBSan crash analysis"""
        crash_info = detector._analyze_execution(
            exit_code=1,
            signal_num=None,
            stdout=b"",
            stderr=b"UndefinedBehaviorSanitizer: runtime error",
            input_data=b"test"
        )
        
        assert crash_info.crashed is True
        assert crash_info.crash_type == CrashType.UBSAN

    def test_analyze_signal_crash(self, detector):
        """Test signal-based crash"""
        crash_info = detector._analyze_execution(
            exit_code=-11,
            signal_num=11,  # SIGSEGV
            stdout=b"",
            stderr=b"",
            input_data=b"test"
        )
        
        assert crash_info.crashed is True
        assert crash_info.crash_type == CrashType.SEGV

    def test_analyze_no_crash(self, detector):
        """Test no crash detection"""
        crash_info = detector._analyze_execution(
            exit_code=0,
            signal_num=None,
            stdout=b"Success",
            stderr=b"",
            input_data=b"test"
        )
        
        assert crash_info.crashed is False

