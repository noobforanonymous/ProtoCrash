"""
Analyze Command Implementation
"""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def run_crash_analysis(crash_dir, classify, dedupe, output_format, verbose):
    """
    Analyze crashes from fuzzing campaign.

    Args:
        crash_dir: Directory containing crashes
        classify: Whether to classify by exploitability
        dedupe: Whether to deduplicate crashes
        output_format: Output format (text or json)
        verbose: Verbosity level
    """
    from protocrash.monitors.crash_classifier import CrashClassifier
    from protocrash.core.types import CrashInfo, CrashType

    console = Console()
    crash_path = Path(crash_dir)

    # Display banner
    console.print(Panel.fit(
        "[bold cyan]ProtoCrash Crash Analysis[/bold cyan]\n"
        "Analyzing discovered crashes",
        border_style="cyan"
    ))

    # Load crashes
    crashes = _load_crashes(crash_path)

    if not crashes:
        console.print(f"[yellow]No crashes found in {crash_dir}[/yellow]")
        return

    console.print(f"[green]Found {len(crashes)} crash file(s)[/green]\n")

    # Classify if requested
    if classify:
        classifier = CrashClassifier()
        for crash in crashes:
            # Create CrashInfo object for classifier
            crash_info = CrashInfo(
                crashed=True,
                crash_type=crash.get('crash_type', CrashType.HANG),
                signal_number=crash.get('signal_number', 0),
                stderr=crash.get('stderr', '').encode() if isinstance(crash.get('stderr'), str) else crash.get('stderr', b''),
                input_data=b''
            )
            crash['exploitability'] = classifier.assess_exploitability(crash_info)
            crash['crash_id'] = classifier.generate_crash_id(crash_info)

    # Deduplicate if requested
    if dedupe:
        original_count = len(crashes)
        crashes = _deduplicate_crashes(crashes)
        console.print(f"[yellow]Deduplication: {original_count} → {len(crashes)} unique crashes[/yellow]\n")

    # Output results
    if output_format == 'json':
        _output_json(crashes, console)
    else:
        _output_text(crashes, console, classify)


def _load_crashes(crash_dir: Path) -> list:
    """Load crash files from directory"""
    crashes = []

    for crash_file in crash_dir.glob("crash_*"):
        # Skip .stderr files
        if crash_file.suffix == '.stderr':
            continue
        if crash_file.is_file():
            crash_data = {
                'file': str(crash_file),
                'name': crash_file.name,
                'size': crash_file.stat().st_size,
                'timestamp': crash_file.stat().st_mtime
            }

            # Try to read stderr/signal info if available
            stderr_file = crash_file.with_suffix('.stderr')
            if stderr_file.exists():
                crash_data['stderr'] = stderr_file.read_text()

            crashes.append(crash_data)

    return crashes


def _deduplicate_crashes(crashes: list) -> list:
    """Deduplicate crashes by crash_id"""
    seen = set()
    unique = []

    for crash in crashes:
        crash_id = crash.get('crash_id', crash['name'])
        if crash_id not in seen:
            seen.add(crash_id)
            unique.append(crash)

    return unique


def _output_text(crashes: list, console: Console, classified: bool):
    """Output crashes in text format"""

    # Create summary table
    table = Table(title="Crash Summary", show_header=True, header_style="bold cyan")
    table.add_column("File", style="cyan", width=30)
    table.add_column("Size", justify="right", style="green", width=10)

    if classified:
        table.add_column("Exploitability", style="bold", width=15)
        table.add_column("Crash ID", style="dim", width=25)

    for crash in crashes:
        row = [
            crash['name'],
            f"{crash['size']:,} bytes"
        ]

        if classified:
            exploitability = crash.get('exploitability', 'UNKNOWN')
            color = _get_exploitability_color(exploitability)
            row.append(f"[{color}]{exploitability}[/{color}]")
            row.append(crash.get('crash_id', 'N/A')[:20] + '...')

        table.add_row(*row)

    console.print(table)

    # Show critical crashes
    if classified:
        critical = [c for c in crashes if c.get('exploitability') == 'CRITICAL']
        if critical:
            console.print(f"\n[bold red]⚠ {len(critical)} CRITICAL crash(es) found![/bold red]")


def _output_json(crashes: list, console: Console):
    """Output crashes in JSON format"""
    output = {
        'total_crashes': len(crashes),
        'crashes': crashes
    }
    console.print_json(data=output)


def _get_exploitability_color(exploitability: str) -> str:
    """Get color for exploitability level"""
    colors = {
        'CRITICAL': 'bold red',
        'HIGH': 'red',
        'MEDIUM': 'yellow',
        'LOW': 'green',
        'UNKNOWN': 'dim'
    }
    return colors.get(exploitability, 'white')
