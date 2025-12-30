"""
Report Command Implementation
"""

from pathlib import Path
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel


def generate_report(campaign_dir, output_format, output_path, verbose):
    """
    Generate fuzzing campaign report.

    Args:
        campaign_dir: Campaign directory with corpus and crashes
        output_format: Report format (text, html, json)
        output_path: Output file path
        verbose: Verbosity level
    """
    console = Console()

    # Display banner
    console.print(Panel.fit(
        "[bold magenta]ProtoCrash Report Generator[/bold magenta]\n"
        f"Generating {output_format.upper()} report",
        border_style="magenta"
    ))

    # Collect campaign data
    campaign_data = _collect_campaign_data(campaign_dir, console)

    # Generate report based on format
    if output_format == 'html':
        _generate_html_report(campaign_data, output_path, console)
    elif output_format == 'json':
        _generate_json_report(campaign_data, output_path, console)
    else:  # text
        _generate_text_report(campaign_data, output_path, console)

    console.print(f"\n[bold green]✓ Report generated: {output_path}[/bold green]")


def _collect_campaign_data(campaign_dir: Path, console: Console) -> dict:
    """Collect all campaign data"""
    if campaign_dir:
        campaign_path = Path(campaign_dir)
        corpus_dir = campaign_path / "corpus"
        crashes_dir = campaign_path / "crashes"
    else:
        corpus_dir = Path("./corpus")
        crashes_dir = Path("./crashes")

    console.print(f"[cyan]Collecting data from campaign...[/cyan]")

    # Count corpus inputs
    corpus_count = len(list(corpus_dir.glob("*"))) if corpus_dir.exists() else 0

    # Load crashes
    crashes = []
    if crashes_dir.exists():
        for crash_file in crashes_dir.glob("crash_*"):
            # Skip .stderr files
            if crash_file.suffix == '.stderr':
                continue
            if crash_file.is_file():
                crashes.append({
                    'name': crash_file.name,
                    'size': crash_file.stat().st_size,
                    'timestamp': datetime.fromtimestamp(crash_file.stat().st_mtime).isoformat()
                })

    console.print(f"[green]Found {corpus_count} corpus inputs, {len(crashes)} crashes[/green]")

    return {
        'timestamp': datetime.now().isoformat(),
        'corpus_count': corpus_count,
        'crash_count': len(crashes),
        'crashes': crashes
    }


def _generate_text_report(data: dict, output_path: str, console: Console):
    """Generate text report"""
    report = f"""
ProtoCrash Fuzzing Campaign Report
{'=' * 50}

Generated: {data['timestamp']}

Campaign Summary:
  Corpus Inputs: {data['corpus_count']}
  Total Crashes: {data['crash_count']}

Crashes:
"""

    for i, crash in enumerate(data['crashes'], 1):
        report += f"  {i}. {crash['name']} ({crash['size']} bytes) - {crash['timestamp']}\n"

    Path(output_path).write_text(report)


def _generate_json_report(data: dict, output_path: str, console: Console):
    """Generate JSON report"""
    Path(output_path).write_text(json.dumps(data, indent=2))


def _generate_html_report(data: dict, output_path: str, console: Console):
    """Generate HTML report using advanced generator"""
    from protocrash.cli.ui.html_generator import generate_advanced_html_report

    # Add required stats structure for advanced generator
    if 'stats' not in data:
        data['stats'] = {
            'total_executions': data.get('total_executions', 0),
            'coverage_edges': data.get('coverage_edges', 0),
            'crash_count': data.get('crash_count', 0),
            'exec_per_sec': data.get('exec_per_sec', 0)
        }

    # Generate advanced HTML report with Chart.js
    generate_advanced_html_report(data, output_path)
