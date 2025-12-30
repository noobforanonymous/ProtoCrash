"""
Fuzz Command Implementation
"""

from pathlib import Path
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def run_fuzz_campaign(target, protocol, corpus_dir, crashes_dir, timeout_ms,
                      num_workers, duration, max_iterations, verbose):
    """
    Run fuzzing campaign with specified configuration.

    Args:
        target: Target binary or server
        protocol: Protocol type
        corpus_dir: Corpus directory path
        crashes_dir: Crashes output directory
        timeout_ms: Execution timeout in milliseconds
        num_workers: Number of parallel workers
        duration: Campaign duration in seconds (optional)
        max_iterations: Maximum iterations (optional)
        verbose: Verbosity level
    """
    from protocrash.fuzzing_engine.coordinator import FuzzingConfig, FuzzingCoordinator
    from protocrash.distributed import DistributedCoordinator

    console = Console()

    # Create corpus and crashes directories if they don't exist
    Path(corpus_dir).mkdir(parents=True, exist_ok=True)
    Path(crashes_dir).mkdir(parents=True, exist_ok=True)

    # Display banner
    console.print(Panel.fit(
        "[bold cyan]ProtoCrash Fuzzing Campaign[/bold cyan]\\n"
        "Coverage-Guided Protocol Fuzzer",
        border_style="cyan"
    ))

    # Display configuration
    config_table = Table(title="Configuration", show_header=False)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")

    config_table.add_row("Target", str(target))
    config_table.add_row("Protocol", protocol)
    config_table.add_row("Corpus", corpus_dir)
    config_table.add_row("Crashes", crashes_dir)
    config_table.add_row("Timeout", f"{timeout_ms}ms")
    config_table.add_row("Workers", str(num_workers))
    if duration:
        config_table.add_row("Duration", f"{duration}s")
    if max_iterations:
        config_table.add_row("Max Iterations", str(max_iterations))

    console.print(config_table)
    console.print()

    # Validate inputs with helpful error messages
    validation_errors = _validate_inputs(target, corpus_dir, timeout_ms, num_workers, console)
    if validation_errors:
        for error in validation_errors:
            console.print(f"[bold red]✗ {error}[/bold red]")
        console.print("\n[yellow]💡 Tip: Run 'protocrash fuzz --help' for usage examples[/yellow]")
        sys.exit(1)

    # Parse target
    target_cmd = _parse_target(target, console)

    try:
        # Create fuzzing configuration
        config = FuzzingConfig(
            target_cmd=target_cmd,
            corpus_dir=corpus_dir,
            crashes_dir=crashes_dir,
            timeout_ms=timeout_ms,
            max_iterations=max_iterations,
            stats_interval=10
        )

        if num_workers > 1:
            # Distributed fuzzing
            console.print(f"[bold green]Starting distributed fuzzing with {num_workers} workers...[/bold green]")
            console.print("[yellow]Note: Real-time dashboard available via separate viewer.[/yellow]")
            console.print()

            coordinator = DistributedCoordinator(config, num_workers=num_workers)
            coordinator.run(duration=duration)

        else:
            # Single-process fuzzing
            console.print("[bold green]Starting single-process fuzzing...[/bold green]")
            console.print("[yellow]Tip: Use --workers N for parallel fuzzing.[/yellow]")
            console.print()

            # Note: Real-time dashboard can be viewed using 'protocrash report --live'
            coordinator = FuzzingCoordinator(config)
            coordinator.run()

        console.print("\\n[bold green]✓ Fuzzing campaign completed successfully![/bold green]")

    except KeyboardInterrupt:
        console.print("\\n[yellow]Fuzzing campaign interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\\n[bold red]Error: {e}[/bold red]")
        if verbose > 0:
            console.print_exception()
        sys.exit(1)


def _validate_inputs(target, corpus_dir, timeout_ms, num_workers, console):
    """Validate fuzzing inputs and return list of errors"""
    errors = []

    # Validate target
    if not target:
        errors.append("Target cannot be empty")
    elif not target.startswith(("tcp://", "udp://")):
        # Binary target - check if file exists
        target_path = Path(target)
        if not target_path.exists():
            errors.append(f"Target binary not found: {target}")
            errors.append(f"  → Check the path or use absolute path")
        elif not target_path.is_file():
            errors.append(f"Target is not a file: {target}")
        elif not target_path.stat().st_mode & 0o111:
            console.print(f"[yellow]⚠ Warning: Target may not be executable: {target}[/yellow]")

    # Validate corpus directory
    corpus_path = Path(corpus_dir)
    if corpus_path.exists():
        seeds = list(corpus_path.glob("*"))
        if not seeds:
            console.print(f"[yellow]⚠ Warning: Corpus directory is empty: {corpus_dir}[/yellow]")
            console.print(f"[yellow]  → Add seed files or fuzzer will generate random inputs[/yellow]")

    # Validate timeout
    if timeout_ms <= 0:
        errors.append(f"Timeout must be positive, got: {timeout_ms}ms")
    elif timeout_ms < 100:
        console.print(f"[yellow]⚠ Warning: Very short timeout ({timeout_ms}ms) may cause false positives[/yellow]")
    elif timeout_ms > 60000:
        console.print(f"[yellow]⚠ Warning: Long timeout ({timeout_ms}ms) will slow fuzzing[/yellow]")

    # Validate workers
    if num_workers <= 0:
        errors.append(f"Number of workers must be positive, got: {num_workers}")
    elif num_workers > 32:
        console.print(f"[yellow]⚠ Warning: {num_workers} workers may overwhelm system[/yellow]")

    return errors


def _parse_target(target: str, console) -> list:
    """
    Parse target specification into command list.

    Args:
        target: Target specification (binary path or tcp://host:port)
        console: Rich console for warnings

    Returns:
        Command list for FuzzingConfig

    Note:
        Network fuzzing (tcp://, udp://) requires protocol-specific
        implementation and is planned for future releases.
    """
    if target.startswith(("tcp://", "udp://")):
        # Network target - currently treated as command placeholder
        console.print("[yellow]⚠ Network fuzzing is experimental[/yellow]")
        console.print("[yellow]  → Ensure target server is running and accessible[/yellow]")
        return [target]
    else:
        # Binary target - @@ will be replaced with input file
        return [target, "@@"]
