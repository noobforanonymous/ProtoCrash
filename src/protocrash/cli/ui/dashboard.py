"""
Real-Time Fuzzing Dashboard using Rich with Keyboard Controls
"""
import time
from datetime import timedelta
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.text import Text
class FuzzingDashboard:
    """Live fuzzing campaign dashboard with keyboard controls"""
    def __init__(self, stats_aggregator, num_workers=1):
        """
        Initialize dashboard.
        Args:
            stats_aggregator: StatsAggregator instance
            num_workers: Number of fuzzing workers
        """
        self.console = Console()
        self.stats = stats_aggregator
        self.num_workers = num_workers
        self.start_time = time.time()
        self.running = True
    def create_layout(self) -> Layout:
        """Create dashboard layout"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="progress", size=3),
            Layout(name="stats", size=10),
            Layout(name="workers", size=10) if self.num_workers > 1 else Layout(name="empty", size=0),
            Layout(name="footer", size=2)
        )
        return layout
    def generate_header(self) -> Panel:
        """Generate header panel"""
        elapsed = timedelta(seconds=int(time.time() - self.start_time))
        header_text = Text()
        header_text.append("ProtoCrash Fuzzing Campaign", style="bold cyan")
        header_text.append(f" • {self.num_workers} Worker{'s' if self.num_workers > 1 else ''}", style="green")
        header_text.append(f" • Elapsed: {elapsed}", style="yellow")
        return Panel(header_text, border_style="cyan")
    def generate_progress_bar(self, duration=None) -> Panel:
        """Generate progress bar for timed campaigns"""
        if not duration:
            return Panel(Text("Continuous fuzzing (no time limit)", style="dim"), border_style="dim")
        elapsed = time.time() - self.start_time
        progress_pct = min(100, (elapsed / duration) * 100)
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn()
        )
        task = progress.add_task("Campaign Progress", total=duration, completed=elapsed)
        return Panel(progress, border_style="green" if progress_pct < 90 else "yellow")
    def generate_stats_table(self) -> Table:
        """Generate statistics table"""
        table = Table(title="Campaign Statistics", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Value", justify="right", style="green", width=15)
        table.add_column("Rate", justify="right", style="yellow", width=15)
        stats = self.stats.get_aggregate_stats()
        # Total executions
        table.add_row(
            "Total Executions",
            f"{stats['total_executions']:,}",
            f"{stats.get('avg_exec_per_sec', 0):,.0f}/sec"
        )
        # Coverage
        table.add_row(
            "Coverage Edges",
            f"{stats.get('coverage_edges', 0):,}",
            ""
        )
        # Crashes
        table.add_row(
            "Unique Crashes",
            f"{stats['total_crashes']:,}",
            f"{'+' + str(stats.get('recent_crashes', 0)) if stats.get('recent_crashes') else ''}"
        )
        # Hangs
        table.add_row(
            "Timeouts/Hangs",
            f"{stats['total_hangs']:,}",
            ""
        )
        return table
    def generate_worker_table(self) -> Table:
        """Generate per-worker statistics table"""
        table = Table(title="Worker Status", show_header=True, header_style="bold magenta")
        table.add_column("Worker", style="magenta", width=12)
        table.add_column("Executions", justify="right", style="green", width=15)
        table.add_column("Exec/sec", justify="right", style="yellow", width=12)
        table.add_column("Crashes", justify="right", style="red", width=10)
        table.add_column("Status", justify="center", width=10)
        inactive_workers = self.stats.get_inactive_workers(timeout=10.0)
        for worker_id, worker_stats in sorted(self.stats.worker_stats.items()):
            status = "[red]INACTIVE[/red]" if worker_id in inactive_workers else "[green]ACTIVE[/green]"
            table.add_row(
                f"Worker {worker_id}",
                f"{worker_stats.executions:,}",
                f"{worker_stats.get_exec_per_sec():,.0f}",
                f"{worker_stats.crashes}",
                status
            )
        return table
    def generate_footer(self, paused=False) -> Panel:
        """Generate footer with controls"""
        if paused:
            footer_text = Text()
            footer_text.append("[PAUSED] Press ", style="bold yellow")
            footer_text.append("P", style="bold red")
            footer_text.append(" to resume | ", style="bold yellow")
            footer_text.append("R", style="bold red")
            footer_text.append(" to refresh | ", style="bold yellow")
            footer_text.append("Q", style="bold red")
            footer_text.append(" to quit", style="bold yellow")
            return Panel(footer_text, border_style="yellow")
        else:
            footer_text = Text()
            footer_text.append("Controls: ", style="dim")
            footer_text.append("P", style="bold green")
            footer_text.append("=pause ", style="dim")
            footer_text.append("R", style="bold green")
            footer_text.append("=refresh ", style="dim")
            footer_text.append("Q", style="bold green")
            footer_text.append("=quit | ", style="dim")
            footer_text.append("Ctrl+C", style="bold red")
            footer_text.append(" to stop", style="dim")
            return Panel(footer_text, border_style="dim")
    def update_layout(self, layout: Layout, duration=None, paused=False):
        """Update layout with current stats"""
        layout["header"].update(self.generate_header())
        layout["progress"].update(self.generate_progress_bar(duration))
        layout["stats"].update(self.generate_stats_table())
        if self.num_workers > 1:
            layout["workers"].update(self.generate_worker_table())
        layout["footer"].update(self.generate_footer(paused))
    def run(self, duration=None, update_interval=1.0):
        """
        Run live dashboard with keyboard controls.
        Args:
            duration: Campaign duration in seconds (optional)
            update_interval: Update frequency in seconds
        Keyboard Controls:
            - P: Pause/Resume
            - R: Force refresh
            - Q: Quit
            - Ctrl+C: Stop fuzzing
        """
        from protocrash.cli.ui.keyboard_handler import KeyboardHandler
        layout = self.create_layout()
        kb_handler = KeyboardHandler()
        kb_handler.start()
        try:
            with Live(layout, console=self.console, refresh_per_second=1) as live:
                while self.running and kb_handler.running:
                    # Handle keyboard events
                    paused = kb_handler.paused
                    if kb_handler.should_refresh:
                        kb_handler.should_refresh = False
                        # Force refresh by updating layout
                    # Update display (even when paused to show status)
                    self.update_layout(layout, duration, paused)
                    # Check if duration exceeded
                    if duration and time.time() - self.start_time >= duration:
                        break
                    time.sleep(update_interval)
        except KeyboardInterrupt:
            self.running = False
        finally:
            kb_handler.stop()
