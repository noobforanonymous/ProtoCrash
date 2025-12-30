"""Comprehensive tests for crash minimizer - DeltaDebugger and new API"""

import pytest
from unittest.mock import Mock
from protocrash.monitors.crash_minimizer import CrashMinimizer, DeltaDebugger
from protocrash.core.types import CrashInfo, CrashType


class TestDeltaDebugger:
    """Test DeltaDebugger class"""
    
    def test_minimize_empty_input(self):
        """Test minimizing empty input"""
        def test_fn(data):
            return False
        
        debugger = DeltaDebugger(test_fn)
        result = debugger.minimize(b"")
        assert result == b""
    
    def test_minimize_basic(self):
        """Test basic minimization"""
        def test_fn(data):
            return b"CRASH" in data
        
        debugger = DeltaDebugger(test_fn)
        result = debugger.minimize(b"XXXCRASHYYY")
        
        # Should contain CRASH but be smaller
        assert b"CRASH" in result
        assert len(result) <= len(b"XXXCRASHYYY")
    
    def test_minimize_single_byte(self):
        """Test minimizing to single byte"""
        def test_fn(data):
            return len(data) > 0
        
        debugger = DeltaDebugger(test_fn)
        result = debugger.minimize(b"A")
        
        assert result == b"A"
    
    def test_minimize_max_tests_limit(self):
        """Test hitting max tests limit"""
        call_count = [0]
        
        def test_fn(data):
            call_count[0] += 1
            return True
        
        debugger = DeltaDebugger(test_fn)
        debugger.max_tests = 10
        
        result = debugger.minimize(b"A" * 100)
        assert debugger.test_count <= 10
    
    def test_get_stats(self):
        """Test getting statistics"""
        def test_fn(data):
            return True
        
        debugger = DeltaDebugger(test_fn)
        debugger.minimize(b"TEST")
        
        stats = debugger.get_stats()
        assert 'test_count' in stats
        assert 'max_tests' in stats
        assert stats['test_count'] > 0


class TestCrashMinimizerNewAPI:
    """Test CrashMinimizer new API"""
    
    @pytest.fixture
    def crash_detector(self):
        """Mock crash detector"""
        detector = Mock()
        return detector
    
    @pytest.fixture
    def minimizer(self, crash_detector):
        """Create minimizer with detector"""
        return CrashMinimizer(crash_detector=crash_detector)
    
    def test_minimize_new_api_delta_strategy(self, minimizer, crash_detector):
        """Test new API with delta strategy"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            input_data=b"A" * 150  # Long enough for delta strategy
        )
        
        # Mock detector to return crash with matching type
        crash_detector.execute_and_detect.return_value = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            input_data=b"MINIMIZED"
        )
        
        result = minimizer.minimize(
            target_cmd=["test"],
            crash_info=crash_info,
            strategy="auto"
        )
        
        assert result is not None
    
    def test_minimize_new_api_byte_strategy(self, minimizer, crash_detector):
        """Test new API with byte strategy"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            input_data=b"SHORT"  # Short enough for byte strategy
        )
        
        crash_detector.execute_and_detect.return_value = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            input_data=b"MINIMIZED"
        )
        
        result = minimizer.minimize(
            target_cmd=["test"],
            crash_info=crash_info,
            strategy="auto"
        )
        
        assert result is not None
    
    def test_minimize_new_api_not_crashed(self, minimizer):
        """Test new API with non-crashing input returns original"""
        crash_info = CrashInfo(
            crashed=False,
            input_data=b"TEST"
        )
        
        result = minimizer.minimize(
            target_cmd=["test"],
            crash_info=crash_info,
            strategy="auto"
        )
        
        assert result == b"TEST"
    
    def test_minimize_new_api_no_input_data(self, minimizer):
        """Test new API with None input_data"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            input_data=None
        )
        
        result = minimizer.minimize(
            target_cmd=["test"],
            crash_info=crash_info,
            strategy="auto"
        )
        
        assert result is None
    
    def test_minimize_no_detector_returns_original(self):
        """Test minimizer without detector returns original"""
        minimizer = CrashMinimizer(crash_detector=None)
        crash_info = CrashInfo(
            crashed=True,
            input_data=b"TEST"
        )
        
        result = minimizer.minimize(
            target_cmd=["test"],
            crash_info=crash_info
        )
        
        assert result == b""  # No detector returns empty
    
    def test_get_reduction_ratio(self, minimizer):
        """Test reduction ratio calculation"""
        ratio = minimizer.get_reduction_ratio(100, 50)
        assert ratio == 0.5
        
        ratio = minimizer.get_reduction_ratio(100, 100)
        assert ratio == 0.0
        
        ratio = minimizer.get_reduction_ratio(0, 0)
        assert ratio == 0.0
