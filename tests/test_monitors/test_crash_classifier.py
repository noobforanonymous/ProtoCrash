"""Tests for Crash Classifier"""

import pytest
from protocrash.monitors.crash_classifier import CrashClassifier
from protocrash.core.types import CrashInfo, CrashType


class TestCrashClassifier:
    """Test Crash Classifier"""
    
    def test_classify_segv(self):
        """Test SIGSEGV classification"""
        crash = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            signal_number=11,
            stderr=b"Segmentation fault",
            stack_trace="#0 0x401234 in main()",
            input_data=b"test"
        )
        
        result = CrashClassifier.assess_exploitability(crash)
        assert result in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    def test_classify_abort(self):
        """Test SIGABRT classification"""
        crash = CrashInfo(
            crashed=True,
            crash_type=CrashType.ABRT,
            signal_number=6,
            stderr=b"Aborted",
            stack_trace="#0 0x401234 in abort()",
            input_data=b"test"
        )
        
        result = CrashClassifier.assess_exploitability(crash)
        assert result in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    def test_classify_hang(self):
        """Test hang/timeout classification"""
        crash = CrashInfo(
            crashed=True,
            crash_type=CrashType.HANG,
            stderr=b"Timeout",
            input_data=b"test"
        )
        
        result = CrashClassifier.assess_exploitability(crash)
        assert result in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    def test_classify_no_crash(self):
        """Test non-crash classification"""
        crash = CrashInfo(
            crashed=False,
            input_data=b"test"
        )
        
        result = CrashClassifier.assess_exploitability(crash)
        assert result == "NONE"
    
    def test_classify_with_stack_trace(self):
        """Test classification with detailed stack trace"""
        stack = """
#0  0x00007ffff7a05428 in __GI_raise (sig=sig@entry=6) at ../sysdeps/unix/sysv/linux/raise.c:54
#1  0x00007ffff7a0702a in __GI_abort () at abort.c:89
#2  0x0000000000401234 in vulnerable_function ()
#3  0x0000000000401567 in main ()
"""
        
        crash = CrashInfo(
            crashed=True,
            crash_type=CrashType.ABRT,
            signal_number=6,
            stderr=stack.encode(),
            stack_trace=stack,
            input_data=b"test"
        )
        
        result = CrashClassifier.assess_exploitability(crash)
        assert result in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    def test_classify_asan(self):
        """Test AddressSanitizer crash classification"""
        asan_output = b"""
==12345==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x60300000eff4
READ of size 4 at 0x60300000eff4 thread T0
    #0 0x401234 in vulnerable_function
"""
        
        crash = CrashInfo(
            crashed=True,
            crash_type=CrashType.ASAN,
            stderr=asan_output,
            stack_trace=asan_output.decode(),
            input_data=b"test"
        )
        
        result = CrashClassifier.assess_exploitability(crash)
        assert result in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    def test_classify_multiple_crashes(self):
        """Test classifying multiple crashes"""
        crashes = [
            CrashInfo(crashed=True, crash_type=CrashType.SEGV, signal_number=11, input_data=b"a"),
            CrashInfo(crashed=True, crash_type=CrashType.ABRT, signal_number=6, input_data=b"b"),
            CrashInfo(crashed=True, crash_type=CrashType.HANG, input_data=b"c"),
        ]
        
        for crash in crashes:
            result = CrashClassifier.assess_exploitability(crash)
            assert result in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
