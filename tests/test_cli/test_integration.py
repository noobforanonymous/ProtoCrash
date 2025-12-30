"""
Integration tests for CLI end-to-end workflows
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
import shutil
import time


class TestFuzzingWorkflow:
    """Test complete fuzzing workflows"""
    
    def test_full_fuzzing_to_report_workflow(self):
        """Test complete workflow: fuzz → analyze → report"""
        from protocrash.cli.main import cli
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir) / 'corpus'
            crashes_dir = Path(tmpdir) / 'crashes'
            corpus_dir.mkdir()
            crashes_dir.mkdir()
            
            # Create sample corpus
            (corpus_dir / 'seed1').write_bytes(b'test data 1')
            (corpus_dir / 'seed2').write_bytes(b'test data 2')
            
            # Create sample crashes (for workflow testing)
            (crashes_dir / 'crash_001').write_bytes(b'crash data 1')
            (crashes_dir / 'crash_002').write_bytes(b'crash data 2')
            (crashes_dir / 'crash_001.stderr').write_text('SIGSEGV at 0x41414141')
            
            # Step 1: Analyze crashes
            result = runner.invoke(cli, [
                'analyze',
                '--crash-dir', str(crashes_dir),
                '--classify'
            ])
            assert result.exit_code == 0
            assert 'crash' in result.output.lower()
            
            # Step 2: Generate text report
            report_path = Path(tmpdir) / 'report.txt'
            result = runner.invoke(cli, [
                'report',
                '--campaign', tmpdir,
                '--format', 'text',
                '--output', str(report_path)
            ])
            assert result.exit_code == 0
            assert report_path.exists()
            content = report_path.read_text()
            assert 'ProtoCrash' in content
            assert 'Corpus Inputs: 2' in content
            assert 'Total Crashes: 2' in content
            
            # Step 3: Generate HTML report
            html_path = Path(tmpdir) / 'report.html'
            result = runner.invoke(cli, [
                'report',
                '--campaign', tmpdir,
                '--format', 'html',
                '--output', str(html_path)
            ])
            assert result.exit_code == 0
            assert html_path.exists()
            html_content = html_path.read_text()
            assert '<html' in html_content.lower()
            assert 'ProtoCrash' in html_content
            
            # Step 4: Generate JSON report
            json_path = Path(tmpdir) / 'report.json'
            result = runner.invoke(cli, [
                'report',
                '--campaign', tmpdir,
                '--format', 'json',
                '--output', str(json_path)
            ])
            assert result.exit_code == 0
            assert json_path.exists()
            
            import json
            data = json.loads(json_path.read_text())
            assert data['corpus_count'] == 2
            assert data['crash_count'] == 2


class TestCrashAnalysisWorkflow:
    """Test crash analysis workflows"""
    
    def test_crash_classification_workflow(self):
        """Test crash classification and deduplication"""
        from protocrash.cli.main import cli
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            crashes_dir = Path(tmpdir)
            
            # Create multiple crashes with different signals
            (crashes_dir / 'crash_001').write_bytes(b'A' * 100)
            (crashes_dir / 'crash_001.stderr').write_text('SIGSEGV - segmentation fault\n#0 0x41414141')
            
            (crashes_dir / 'crash_002').write_bytes(b'B' * 200)
            (crashes_dir / 'crash_002.stderr').write_text('SIGABRT - abort\n#0 0x00007fff')
            
            (crashes_dir / 'crash_003').write_bytes(b'A' * 100)  # Duplicate of 001
            (crashes_dir / 'crash_003.stderr').write_text('SIGSEGV - segmentation fault\n#0 0x41414141')
            
            # Analyze with classification
            result = runner.invoke(cli, [
                'analyze',
                '--crash-dir', str(crashes_dir),
                '--classify',
                '--dedupe'
            ])
            
            assert result.exit_code == 0
            assert 'SIGSEGV' in result.output or 'crash' in result.output.lower()


class TestReportGenerationWorkflow:
    """Test report generation with different formats"""
    
    def test_html_report_with_charts(self):
        """Test HTML report includes Chart.js visualizations"""
        from protocrash.cli.main import cli
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir) / 'corpus'
            crashes_dir = Path(tmpdir) / 'crashes'
            corpus_dir.mkdir()
            crashes_dir.mkdir()
            
            # Create data
            for i in range(5):
                (corpus_dir / f'seed_{i}').write_bytes(f'data {i}'.encode())
                (crashes_dir / f'crash_{i:03d}').write_bytes(f'crash {i}'.encode())
            
            # Generate HTML report
            html_path = Path(tmpdir) / 'advanced_report.html'
            result = runner.invoke(cli, [
                'report',
                '--campaign', tmpdir,
                '--format', 'html',
                '--output', str(html_path)
            ])
            
            assert result.exit_code == 0
            assert html_path.exists()
            
            content = html_path.read_text()
            # Check for Chart.js
            assert 'chart.js' in content.lower() or 'chart' in content.lower()
            # Check for metrics
            assert '5' in content  # corpus count
            # Check for styling
            assert 'style' in content.lower()
    
    def test_json_report_structure(self):
        """Test JSON report has correct structure"""
        from protocrash.cli.main import cli
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / 'report.json'
            result = runner.invoke(cli, [
                'report',
                '--format', 'json',
                '--output', str(json_path)
            ])
            
            assert result.exit_code == 0
            
            import json
            data = json.loads(json_path.read_text())
            
            # Verify structure
            assert 'timestamp' in data
            assert 'corpus_count' in data
            assert 'crash_count' in data
            assert 'crashes' in data
            assert isinstance(data['crashes'], list)


class TestCLIErrorHandling:
    """Test CLI error handling"""
    
    def test_missing_required_arguments(self):
        """Test CLI handles missing required arguments"""
        from protocrash.cli.main import cli
        runner = CliRunner()
        
        # Fuzz without target
        result = runner.invoke(cli, ['fuzz'])
        assert result.exit_code != 0
        
        # Analyze without crash-dir
        result = runner.invoke(cli, ['analyze'])
        assert result.exit_code != 0
        
        # Report without output
        result = runner.invoke(cli, ['report', '--format', 'html'])
        assert result.exit_code != 0
    
    def test_invalid_crash_directory(self):
        """Test handling of non-existent crash directory"""
        from protocrash.cli.main import cli      
        runner = CliRunner()
        
        result = runner.invoke(cli, [
            'analyze',
            '--crash-dir', '/nonexistent/path'
        ])
        assert result.exit_code != 0


class TestCrossModuleIntegration:
    """Test integration between different modules"""
    
    def test_crash_viewer_with_analyzer(self):
        """Test crash viewer integration with analyzer"""
        from protocrash.cli.ui.crash_viewer import CrashReportViewer
        from protocrash.monitors.crash_classifier import CrashClassifier
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test crash
            crash_file = Path(tmpdir) / 'crash_test'
            crash_file.write_bytes(b'test crash data')
            stderr_file = crash_file.with_suffix('.stderr')
            stderr_file.write_text("""
SIGSEGV - Segmentation fault
#0  0x00007fff8badc0de in vulnerable_func () at target.c:42
#1  0x00007fff8badc123 in main () at target.c:10
rax: 0x4141414141414141  rbx: 0x00007fff8bad0000
rip: 0x00007fff8badc0de  rsp: 0x00007fffffffe000
""")
            
            # Load and analyze
            viewer = CrashReportViewer(tmpdir)
            crashes = viewer.load_crashes()
            
            assert len(crashes) == 1
            assert crashes[0]['signal']
            assert crashes[0]['stack_trace']
            assert crashes[0]['registers']
            assert 'RIP' in crashes[0]['registers']
    
    def test_stats_aggregator_with_dashboard(self):
        """Test stats aggregator integration with dashboard"""
        from protocrash.distributed.stats_aggregator import StatsAggregator, WorkerStats
        from protocrash.cli.ui.dashboard import FuzzingDashboard
        from protocrash.fuzzing_engine.stats import FuzzingStats
        
        # Create aggregator with sample data
        aggregator = StatsAggregator(num_workers=1)
        
        # Create FuzzingStats object with correct API
        stats = FuzzingStats()
        stats.total_execs = 1000
        stats.unique_crashes = 5
        stats.unique_hangs = 2
        stats.timeouts = 0
        stats.corpus_size = 100
        stats.coverage_edges = 150
        
        aggregator.update_worker_stats(0, stats)
        
        # Create dashboard
        dashboard = FuzzingDashboard(aggregator, num_workers=1)
        
        # Verify dashboard can access stats
        agg_stats = dashboard.stats.get_aggregate_stats()
        assert agg_stats['total_executions'] == 1000
        assert agg_stats['total_crashes'] == 5
        assert agg_stats['total_hangs'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
