"""Comprehensive tests for CrashReporter new API - HTML/Markdown generation"""

import pytest
import json
from pathlib import Path
from protocrash.monitors.crash_reporter import CrashReporter
from protocrash.monitors.crash_bucketing import CrashBucket
from protocrash.monitors.stack_trace_parser import StackTrace
from protocrash.core.types import CrashInfo, CrashType


class TestCrashReporterAdvanced:
    """Test advanced CrashReporter features"""

    @pytest.fixture
    def reporter(self, tmp_path):
        return CrashReporter(tmp_path / "reports")

    @pytest.fixture
    def sample_bucket(self):
        # Create stack trace without frames for simplicity
        stack_trace = None  # Simpler approach
        
        return CrashBucket(
            bucket_id="test_bucket",
            crash_hash="abc123",
            crash_type="SEGV",
            exploitability="HIGH",
            count=5,
            first_seen="2024-01-01T00:00:00",
            last_seen="2024-01-02T00:00:00",
            stack_trace=stack_trace
        )

    @pytest.fixture
    def sample_crash_info(self):
        return CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            signal_number=11,
            exit_code=-11,
            stderr=b"Segmentation fault at 0xdeadbeef",
            input_data=b"CRASH_TRIGGER_DATA"
        )

    def test_generate_json_report(self, reporter, sample_bucket, sample_crash_info):
        """Test JSON report generation"""
        report_path = reporter.generate_crash_report(
            sample_bucket,
            sample_crash_info,
            format="json"
        )
        
        assert Path(report_path).exists()
        assert report_path.endswith(".json")
        
        # Verify JSON structure
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        assert 'timestamp' in data
        assert data['bucket_id'] == sample_bucket.bucket_id
        assert data['crash_hash'] == sample_bucket.crash_hash
        assert data['crash_type'] == sample_bucket.crash_type
        assert data['exploitability'] == sample_bucket.exploitability
        assert data['count'] == sample_bucket.count

    def test_generate_html_report(self, reporter, sample_bucket, sample_crash_info):
        """Test HTML report generation"""
        report_path = reporter.generate_crash_report(
            sample_bucket,
            sample_crash_info,
            format="html"
        )
        
        assert Path(report_path).exists()
        assert report_path.endswith(".html")
        
        # Verify HTML content
        with open(report_path, 'r') as f:
            content = f.read()
        
        assert "<!DOCTYPE html>" in content
        assert sample_bucket.crash_type in content
        assert sample_bucket.exploitability in content
        assert sample_bucket.crash_hash in content

    def test_generate_html_report_saves_input(self, reporter, sample_bucket, sample_crash_info):
        """Test HTML report saves input file"""
        report_path = reporter.generate_crash_report(
            sample_bucket,
            sample_crash_info,
            format="html"
        )
        
        # Check input file was saved
        input_path = reporter.output_dir / f"crash_{sample_bucket.crash_hash}.input"
        assert input_path.exists()
        assert input_path.read_bytes() == sample_crash_info.input_data

    def test_generate_markdown_report(self, reporter, sample_bucket, sample_crash_info):
        """Test Markdown report generation"""
        report_path = reporter.generate_crash_report(
            sample_bucket,
            sample_crash_info,
            format="markdown"
        )
        
        assert Path(report_path).exists()
        assert report_path.endswith(".md")
        
        # Verify Markdown content
        with open(report_path, 'r') as f:
            content = f.read()
        
        assert "# Crash Report:" in content
        assert sample_bucket.crash_type in content
        assert sample_bucket.exploitability in content

    def test_generate_report_unknown_format(self, reporter, sample_bucket, sample_crash_info):
        """Test unknown format raises error"""
        with pytest.raises(ValueError, match="Unknown format"):
            reporter.generate_crash_report(
                sample_bucket,
                sample_crash_info,
                format="invalid"
            )

    def test_generate_html_summary_report(self, reporter, sample_bucket):
        """Test HTML summary report generation"""
        # Create multiple buckets
        buckets = []
        for i in range(3):
            bucket = CrashBucket(
                bucket_id=f"bucket_{i}",
                crash_hash=f"hash_{i}",
                crash_type="SEGV" if i % 2 == 0 else "HANG",
                exploitability="HIGH" if i == 0 else "MEDIUM",
                count=i + 1,
                first_seen="2024-01-01T00:00:00",
                last_seen="2024-01-01T00:00:00",
                stack_trace=None
            )
            buckets.append(bucket)
        
        report_path = reporter.generate_summary_report(buckets, format="html")
        
        assert Path(report_path).exists()
        assert "crash_summary.html" in report_path
        
        # Verify HTML content
        with open(report_path, 'r') as f:
            content = f.read()
        
        assert "Total unique crashes" in content
        assert "3" in content  # Number of crashes

    def test_generate_markdown_summary_report(self, reporter):
        """Test Markdown summary report generation"""
        buckets = [
            CrashBucket(
                bucket_id="bucket_1",
                crash_hash="hash_1",
                crash_type="SEGV",
                exploitability="HIGH",
                count=10,
                first_seen="2024-01-01T00:00:00",
                last_seen="2024-01-01T00:00:00",
                stack_trace=None
            )
        ]
        
        report_path = reporter.generate_summary_report(buckets, format="markdown")
        
        assert Path(report_path).exists()
        assert "crash_summary.md" in report_path
        
        # Verify Markdown content
        with open(report_path, 'r') as f:
            content = f.read()
        
        assert "# Crash Summary Report" in content
        assert "Total Unique Crashes" in content

    def test_generate_summary_report_unknown_format(self, reporter):
        """Test summary report with unknown format raises error"""
        with pytest.raises(ValueError, match="Unknown format"):
            reporter.generate_summary_report([], format="invalid")

    def test_generate_report_with_none_stderr(self, reporter, sample_bucket):
        """Test report generation with None stderr"""
        crash_info = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            stderr=None,
            input_data=b"test"
        )
        
        report_path = reporter.generate_crash_report(
            sample_bucket,
            crash_info,
            format="json"
        )
        
        assert Path(report_path).exists()

    def test_generate_report_with_none_stack_trace(self, reporter, sample_crash_info):
        """Test report generation with None stack trace"""
        bucket = CrashBucket(
            bucket_id="test",
            crash_hash="test123",
            crash_type="HANG",
            exploitability="LOW",
            count=1,
            first_seen="2024-01-01T00:00:00",
            last_seen="2024-01-01T00:00:00",
            stack_trace=None
        )
        
        report_path = reporter.generate_crash_report(
            bucket,
            sample_crash_info,
            format="html"
        )
        
        assert Path(report_path).exists()
