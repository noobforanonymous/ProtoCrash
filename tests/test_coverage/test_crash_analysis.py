"""Test crash minimizer, classifier, and reporter"""

import pytest
from pathlib import Path
from protocrash.core.types import CrashInfo, CrashType
from protocrash.monitors.crash_minimizer import CrashMinimizer
from protocrash.monitors.crash_classifier import CrashClassifier
from protocrash.monitors.crash_reporter import CrashReporter


class TestCrashMinimizer:
    """Test CrashMinimizer class"""

    @pytest.fixture
    def minimizer(self):
        return CrashMinimizer(None)

    def test_init(self, minimizer):
        """Test initialization"""
        assert minimizer.max_iterations == 10

    def test_minimize_simple(self, minimizer):
        """Test simple minimization"""
        # Crash if input contains "CRASH"
        def crash_fn(data):
            return CrashInfo(crashed=b"CRASH" in data)
        
        original = b"AAACRASHBBB"
        minimized = minimizer.minimize(original, crash_fn)
        
        # Should still crash
        assert crash_fn(minimized).crashed
        # Should be smaller
        assert len(minimized) <= len(original)

    def test_minimize_no_crash(self, minimizer):
        """Test minimization when input doesn't crash"""
        def crash_fn(data):
            return CrashInfo(crashed=False)
        
        original = b"TESTDATA"
        minimized = minimizer.minimize(original, crash_fn)
        
        # Should return original if it doesn't crash
        assert minimized == original

    def test_minimize_single_byte(self, minimizer):
        """Test minimization of single byte"""
        def crash_fn(data):
            return CrashInfo(crashed=len(data) > 0)
        
        original = b"A"
        minimized = minimizer.minimize(original, crash_fn)
        
        assert len(minimized) == 1

    def test_minimize_empty_result(self, minimizer):
        """Test minimization that results in empty"""
        def crash_fn(data):
            # Always crashes, even empty
            return CrashInfo(crashed=True)
        
        original = b"TEST"
        minimized = minimizer.minimize(original, crash_fn)
        
        # Should minimize to empty or very small
        assert len(minimized) <= len(original)


class TestCrashClassifier:
    """Test CrashClassifier class"""

    def test_assess_exploitability_asan_high(self):
        """Test ASan high exploitability"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.ASAN,
            stderr=b"AddressSanitizer: heap-buffer-overflow"
        )
        
        rating = CrashClassifier.assess_exploitability(crash_info)
        assert rating == "HIGH"

    def test_assess_exploitability_ill(self):
        """Test illegal instruction exploitability"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.ILL,
            stderr=b"Illegal instruction"
        )
        
        rating = CrashClassifier.assess_exploitability(crash_info)
        assert rating == "LOW"

    def test_assess_exploitability_fpe(self):
        """Test FPE exploitability"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.FPE,
            stderr=b"Floating point exception"
        )
        
        rating = CrashClassifier.assess_exploitability(crash_info)
        assert rating == "LOW"

    """Test CrashClassifier class"""

    def test_assess_exploitability_high(self):
        """Test high exploitability assessment"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            stderr=b"heap-use-after-free detected"
        )
        
        rating = CrashClassifier.assess_exploitability(crash_info)
        assert rating == "HIGH"

    def test_assess_exploitability_medium(self):
        """Test medium exploitability"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            stderr=b"normal crash"
        )
        
        rating = CrashClassifier.assess_exploitability(crash_info)
        assert rating == "MEDIUM"

    def test_assess_exploitability_low(self):
        """Test low exploitability"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.HANG,
            stderr=b"timeout"
        )
        
        rating = CrashClassifier.assess_exploitability(crash_info)
        assert rating == "LOW"

    def test_assess_exploitability_none(self):
        """Test no crash"""
        crash_info = CrashInfo(crashed=False)
        
        rating = CrashClassifier.assess_exploitability(crash_info)
        assert rating == "NONE"

    def test_generate_crash_id(self):
        """Test crash ID generation"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            signal_number=11,
            stderr=b"ERROR: Segmentation fault"
        )
        
        crash_id = CrashClassifier.generate_crash_id(crash_info)
        
        assert isinstance(crash_id, str)
        assert len(crash_id) == 16  # MD5 hash truncated to 16 chars

    def test_generate_crash_id_deterministic(self):
        """Test crash ID is deterministic"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            stderr=b"ERROR: Same error"
        )
        
        id1 = CrashClassifier.generate_crash_id(crash_info)
        id2 = CrashClassifier.generate_crash_id(crash_info)
        
        assert id1 == id2


class TestCrashReporter:
    """Test CrashReporter class"""

    @pytest.fixture
    def reporter(self, tmp_path):
        return CrashReporter(tmp_path / "crashes")

    def test_init(self, reporter):
        """Test initialization"""
        assert reporter.output_dir.exists()

    def test_save_crash(self, reporter):
        """Test saving crash"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            signal_number=11,
            stderr=b"Segmentation fault",
            input_data=b"TESTINPUT"
        )
        
        report_file = reporter.save_crash(crash_info)
        
        assert report_file.exists()
        assert report_file.suffix == ".json"
        
        # Check input file was saved
        crash_id = report_file.stem
        input_file = reporter.output_dir / f"{crash_id}.input"
        assert input_file.exists()
        assert input_file.read_bytes() == b"TESTINPUT"

    def test_generate_report(self, reporter):
        """Test report generation"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.ASAN,
            exit_code=-6,
            stderr=b"AddressSanitizer: heap-use-after-free",
            input_data=b"TEST"
        )
        
        report = reporter.generate_report(crash_info, "test123")
        
        assert report["crash_id"] == "test123"
        assert report["crashed"] is True
        assert report["crash_type"] == "AddressSanitizer"
        assert report["exploitability"] in ["HIGH", "MEDIUM", "LOW", "NONE"]
        assert "timestamp" in report

    def test_list_crashes(self, reporter):
        """Test listing crashes"""
        # Save a few crashes
        for i in range(3):
            crash_info = CrashInfo(
                crashed=True,
                crash_type=CrashType.SEGV,
                stderr=f"Error {i}".encode(),
                input_data=f"input{i}".encode()
            )
            reporter.save_crash(crash_info, crash_id=f"crash_{i}")
        
        crashes = reporter.list_crashes()
        
        assert len(crashes) == 3
        assert "crash_0" in crashes

    def test_get_crash_report(self, reporter):
        """Test retrieving crash report"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            input_data=b"test"
        )
        
        reporter.save_crash(crash_info, crash_id="test_crash")
        
        report = reporter.get_crash_report("test_crash")
        
        assert report is not None
        assert report["crash_id"] == "test_crash"

    def test_get_crash_report_not_found(self, reporter):
        """Test retrieving nonexistent crash"""
        report = reporter.get_crash_report("nonexistent")
        assert report is None
