"""
Enhanced crash minimization with delta-debugging
"""
from typing import Callable, List
from protocrash.core.types import CrashInfo
class DeltaDebugger:
    """Delta-debugging algorithm for crash minimization"""
    def __init__(self, test_function: Callable[[bytes], bool], timeout_budget: int = 300):
        self.test_function = test_function
        self.timeout_budget = timeout_budget
        self.test_count = 0
        self.max_tests = 10000
    def minimize(self, input_data: bytes) -> bytes:
        """Minimize crashing input using delta-debugging"""
        if len(input_data) == 0:
            return input_data
        current = bytearray(input_data)
        n = 2
        while len(current) > 1 and self.test_count < self.max_tests:
            chunk_size = max(1, len(current) // n)
            reduced = False
            for i in range(0, len(current), chunk_size):
                if self.test_count >= self.max_tests:
                    break
                test_input = current[:i] + current[i + chunk_size:]
                if len(test_input) == 0:
                    continue
                self.test_count += 1
                if self.test_function(bytes(test_input)):
                    current = test_input
                    reduced = True
                    break
            if reduced:
                n = max(2, n - 1)
            else:
                n = min(len(current), n * 2)
                if n > len(current):
                    break
        return bytes(current)
    def get_stats(self) -> dict:
        """Get minimization statistics"""
        return {'test_count': self.test_count, 'max_tests': self.max_tests}
class CrashMinimizer:
    """Enhanced crash minimizer - BACKWARD COMPATIBLE with old API"""
    def __init__(self, crash_detector=None, timeout_budget: int = 300, max_iterations: int = 10):
        self.crash_detector = crash_detector
        self.timeout_budget = timeout_budget
        self.max_iterations = max_iterations
        self.target_cmd = None
        self.original_crash_info = None
    def minimize(
        self,
        original_input: bytes = None,
        crash_fn: Callable = None,
        target_cmd: List[str] = None,
        crash_info: CrashInfo = None,
        strategy: str = "auto"
    ) -> bytes:
        """Minimize crash - supports both old and new API"""
        # Old API compatibility
        if original_input is not None and crash_fn is not None:
            return self._minimize_old_api(original_input, crash_fn)
        # New API
        if target_cmd and crash_info and self.crash_detector:
            return self._minimize_new_api(target_cmd, crash_info, strategy).input_data
        return original_input or b""
    def _minimize_old_api(self, original_input: bytes, crash_fn: Callable) -> bytes:
        """Old API: minimize using crash function"""
        if not crash_fn(original_input).crashed:
            return original_input
        current = original_input
        for iteration in range(self.max_iterations):
            if len(current) <= 1:
                break
            minimized = self._binary_search_minimize(current, crash_fn)
            if minimized == current:
                break
            current = minimized
        current = self._minimize_bytes(current, crash_fn)
        return current
    def _binary_search_minimize(self, data: bytes, crash_fn: Callable) -> bytes:
        """Binary search chunk removal"""
        chunk_size = len(data) // 2
        while chunk_size > 0:
            for pos in range(0, len(data), chunk_size):
                candidate = data[:pos] + data[pos + chunk_size:]
                if candidate and crash_fn(candidate).crashed:
                    return candidate
            chunk_size //= 2
        return data
    def _minimize_bytes(self, data: bytes, crash_fn: Callable) -> bytes:
        """Try setting bytes to simpler values"""
        result = bytearray(data)
        for i in range(len(result)):
            original = result[i]
            if original != 0:
                result[i] = 0
                if crash_fn(bytes(result)).crashed:
                    continue
                result[i] = original
        return bytes(result)
    def _minimize_new_api(self, target_cmd, crash_info, strategy):
        """New API implementation"""
        if not crash_info.crashed or not crash_info.input_data:
            return crash_info
        self.target_cmd = target_cmd
        self.original_crash_info = crash_info
        if strategy == "auto":
            strategy = "delta" if len(crash_info.input_data) >= 100 else "byte"
        def test_crash(input_data: bytes) -> bool:
            test_crash = self.crash_detector.execute_and_detect(target_cmd, input_data)
            return test_crash.crashed and test_crash.crash_type == crash_info.crash_type
        if strategy == "delta":
            debugger = DeltaDebugger(test_crash, self.timeout_budget)
            minimized_input = debugger.minimize(crash_info.input_data)
        else:
            # Byte minimization
            minimized_input = crash_info.input_data
        minimized_crash = self.crash_detector.execute_and_detect(target_cmd, minimized_input)
        return minimized_crash
    def get_reduction_ratio(self, original_size: int, minimized_size: int) -> float:
        """Calculate reduction ratio (0.0-1.0)"""
        if original_size == 0:
            return 0.0
        return (original_size - minimized_size) / original_size
