"""
Unit tests for CLI commands
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
import shutil


def test_cli_help():
    """Test main CLI help"""
    from protocrash.cli.main import cli
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'protocrash' in result.output.lower()
    assert 'fuzz' in result.output.lower()
    assert 'analyze' in result.output.lower()
    assert 'report' in result.output.lower()


def test_fuzz_command_help():
    """Test fuzz command help"""
    from protocrash.cli.main import cli
    runner = CliRunner()
    result = runner.invoke(cli, ['fuzz', '--help'])
    assert result.exit_code == 0
    assert 'target' in result.output.lower()
    assert 'protocol' in result.output.lower()
    assert 'workers' in result.output.lower()


def test_analyze_command_help():
    """Test analyze command help"""
    from protocrash.cli.main import cli
    runner = CliRunner()
    result = runner.invoke(cli, ['analyze', '--help'])
    assert result.exit_code == 0
    assert 'crash-dir' in result.output.lower()
    assert 'classify' in result.output.lower()
    assert 'dedupe' in result.output.lower()


def test_report_command_help():
    """Test report command help"""
    from protocrash.cli.main import cli
    runner = CliRunner()
    result = runner.invoke(cli, ['report', '--help'])
    assert result.exit_code == 0
    assert 'format' in result.output.lower()
    assert 'output' in result.output.lower()


def test_analyze_command_no_crashes():
    """Test analyze command with no crashes"""
    from protocrash.cli.main import cli
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(cli, ['analyze', '--crash-dir', tmpdir])
        assert result.exit_code == 0
        assert 'no crashes' in result.output.lower()


def test_report_generation_text():
    """Test text report generation"""
    from protocrash.cli.main import cli
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / 'report.txt'
        result = runner.invoke(cli, [
            'report',
            '--format', 'text',
            '--output', str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert 'ProtoCrash' in content


def test_report_generation_json():
    """Test JSON report generation"""
    from protocrash.cli.main import cli
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / 'report.json'
        result = runner.invoke(cli, [
            'report',
            '--format', 'json',
            '--output', str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        import json
        data = json.loads(output_file.read_text())
        assert 'timestamp' in data


def test_report_generation_html():
    """Test HTML report generation"""
    from protocrash.cli.main import cli
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / 'report.html'
        result = runner.invoke(cli, [
            'report',
            '--format', 'html',
            '--output', str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert 'ProtoCrash' in content
        assert 'html' in content.lower()


def test_crash_viewer_load():
    """Test crash viewer loading"""
    from protocrash.cli.ui.crash_viewer import CrashReportViewer
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy crash file
        crash_file = Path(tmpdir) / 'crash_001'
        crash_file.write_bytes(b'test data')
        
        viewer = CrashReportViewer(tmpdir)
        crashes = viewer.load_crashes()
        assert len(crashes) == 1
        assert crashes[0]['name'] == 'crash_001'


def test_crash_viewer_filter():
    """Test crash filtering"""
    from protocrash.cli.ui.crash_viewer import CrashReportViewer
    
    crashes = [
        {'signal': 'SIGSEGV', 'size': 100},
        {'signal': 'SIGABRT', 'size': 200},
        {'signal': 'SIGSEGV', 'size': 150}
    ]
    
    viewer = CrashReportViewer('/tmp')
    filtered = viewer.filter_crashes(crashes, signal='SIGSEGV')
    assert len(filtered) == 2


def test_crash_viewer_sort():
    """Test crash sorting"""
    from protocrash.cli.ui.crash_viewer import CrashReportViewer
    
    crashes = [
        {'name': 'crash_c', 'size': 300, 'timestamp': 3},
        {'name': 'crash_a', 'size': 100, 'timestamp': 1},
        {'name': 'crash_b', 'size': 200, 'timestamp': 2}
    ]
    
    viewer = CrashReportViewer('/tmp')
    
    # Sort by size
    sorted_crashes = viewer.sort_crashes(crashes, by='size')
    assert sorted_crashes[0]['size'] == 100
    
    # Sort by name
    sorted_crashes = viewer.sort_crashes(crashes, by='name')
    assert sorted_crashes[0]['name'] == 'crash_a'
