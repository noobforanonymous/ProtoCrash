"""Additional comprehensive tests for crash detection modules"""

import pytest
import signal
from protocrash.core.types import CrashInfo, CrashType
from protocrash.monitors.crash_detector import CrashDetector, SignalHandler, SanitizerMonitor
from protocrash.monitors.crash_classifier import CrashClassifier
from protocrash.monitors.crash_minimizer import CrashMinimizer


class TestCrashDetectorComprehensive:
    """Comprehensive crash detector tests"""

    @pytest.fixture
    def detector(self):
        return CrashDetector(timeout_ms=1000)

    def test_analyze_signal_crash_bus(self, detector):
        """Test BUS signal crash"""
        crash_info = detector._analyze_execution(
            exit_code=-7,
            signal_num=7,  # SIGBUS
            stdout=b"",
            stderr=b"",
            input_data=b"test"
        )
        
        assert crash_info.crashed is True
        assert crash_info.crash_type == CrashType.BUS

    def test_analyze_signal_crash_fpe(self, detector):
        """Test FPE signal crash"""
        crash_info = detector._analyze_execution(
            exit_code=-8,
            signal_num=8,  # SIGFPE
            stdout=b"",
            stderr=b"",
            input_data=b"test"
        )
        
        assert crash_info.crashed is True
        assert crash_info.crash_type == CrashType.FPE

    def test_analyze_signal_crash_ill(self, detector):
        """Test ILL signal crash"""
        crash_info = detector._analyze_execution(
            exit_code=-4,
            signal_num=4,  # SIGILL
            stdout=b"",
            stderr=b"",
            input_data=b"test"
        )
        
        assert crash_info.crashed is True
        assert crash_info.crash_type == CrashType.ILL


class TestCrashClassifierComprehensive:
    """Comprehensive crash classifier tests"""

    def test_assess_asan_medium(self):
        """Test ASan without high-confidence pattern"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.ASAN,
            stderr=b"AddressSanitizer: some error"
        )
        
        rating = CrashClassifier.assess_exploitability(crash_info)
        assert rating in ["MEDIUM", "HIGH"]

    def test_assess_msan_high(self):
        """Test MSan with high-confidence pattern"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.MSAN,
            stderr=b"MemorySanitizer: heap-buffer-overflow"
        )
        
        rating = CrashClassifier.assess_exploitability(crash_info)
        assert rating == "HIGH"

    def test_assess_bus_medium(self):
        """Test BUS exploitability"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.BUS,
            stderr=b"Bus error"
        )
        
        rating = CrashClassifier.assess_exploitability(crash_info)
        assert rating == "MEDIUM"

    def test_assess_abrt_high(self):
        """Test ABRT with high-confidence pattern"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.ABRT,
            stderr=b"stack smashing detected"
        )
        
        rating = CrashClassifier.assess_exploitability(crash_info)
        assert rating == "HIGH"

    def test_crash_id_with_stack_trace(self):
        """Test crash ID generation with stack trace"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            signal_number=11,
            stderr=b"ERROR: Segmentation fault\n#0 main.c:42\n#1 lib.c:100"
        )
        
        crash_id = CrashClassifier.generate_crash_id(crash_info)
        
        assert isinstance(crash_id, str)
        assert len(crash_id) == 16


class TestCrashMinimizerComprehensive:
    """Comprehensive crash minimizer tests"""

    def test_minimize_large_input(self):
        """Test minimizing large input"""
        minimizer = CrashMinimizer(None)
        
        # Large input that crashes if contains "BUG"
        def crash_fn(data):
            return CrashInfo(crashed=b"BUG" in data)
        
        original = b"A" * 100 + b"BUG" + b"Z" * 100
        minimized = minimizer.minimize(original, crash_fn)
        
        assert crash_fn(minimized).crashed
        assert len(minimized) < len(original)
        assert b"BUG" in minimized

    def test_minimize_already_minimal(self):
        """Test minimizing input that's already minimal"""
        minimizer = CrashMinimizer(None)
        
        def crash_fn(data):
            return CrashInfo(crashed=data == b"X")
        
        original = b"X"
        minimized = minimizer.minimize(original, crash_fn)
        
        assert minimized == original

    def test_binary_search_chunk_removal(self):
        """Test binary search chunk removal logic"""
        minimizer = CrashMinimizer(None)
        
        # Crashes if total length > 50
        def crash_fn(data):
            return CrashInfo(crashed=len(data) > 50)
        
        original = b"A" * 100
        minimized = minimizer.minimize(original, crash_fn)
        
        # Should minimize to just above threshold
        assert crash_fn(minimized).crashed
        assert len(minimized) < len(original)


class TestSanitizerMonitorComprehensive:
    """Comprehensive sanitizer monitor tests"""

    def test_detect_stack_buffer_overflow(self):
        """Test stack buffer overflow detection"""
        stderr = b"AddressSanitizer: stack-buffer-overflow on address 0x..."
        assert SanitizerMonitor.detect_asan(stderr) is True

    def test_detect_global_buffer_overflow(self):
        """Test global buffer overflow detection"""
        stderr = b"AddressSanitizer: global-buffer-overflow"
        assert SanitizerMonitor.detect_asan(stderr) is True

    def test_detect_use_after_scope(self):
        """Test use-after-scope detection"""
        stderr = b"AddressSanitizer: use-after-scope detected"
        assert SanitizerMonitor.detect_asan(stderr) is True

    def test_extract_error_with_multiple_lines(self):
        """Test error extraction with multiple error lines"""
        stderr = b"""
        Some output
        ERROR: AddressSanitizer: heap-use-after-free
        More details
        Another ERROR line
        """
        error = SanitizerMonitor.extract_error_type(stderr)
        assert "AddressSanitizer" in error or "ERROR" in error
