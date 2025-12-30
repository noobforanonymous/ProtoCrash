"""
Crash Report Viewer - Detailed crash inspection and comparison
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text
from rich.layout import Layout
from rich.prompt import Prompt


class CrashReportViewer:
    """Detailed crash report viewer with stack traces and comparison"""

    def __init__(self, crash_dir):
        self.crash_dir = Path(crash_dir)
        self.console = Console()
        self.crashes = []

    def load_crashes(self):
        """Load all crashes from directory"""
        self.crashes = []

        for crash_file in sorted(self.crash_dir.glob("crash_*")):
            # Skip .stderr files
            if crash_file.suffix == '.stderr':
                continue
            if crash_file.is_file():
                crash = self._parse_crash_file(crash_file)
                self.crashes.append(crash)

        return self.crashes

    def _parse_crash_file(self, crash_file: Path) -> dict:
        """Parse crash file and associated metadata"""
        crash = {
            'file': crash_file,
            'name': crash_file.name,
            'size': crash_file.stat().st_size,
            'timestamp': crash_file.stat().st_mtime,
            'data': crash_file.read_bytes()
        }

        # Load stderr if available
        stderr_file = crash_file.with_suffix('.stderr')
        if stderr_file.exists():
            crash['stderr'] = stderr_file.read_text()
            crash['stack_trace'] = self._extract_stack_trace(crash['stderr'])
            crash['signal'] = self._extract_signal(crash['stderr'])
            crash['registers'] = self._extract_registers(crash['stderr'])

        return crash

    def _extract_stack_trace(self, stderr: str) -> str:
        """Extract stack trace from stderr"""
        lines = stderr.split('\n')
        stack_lines = []
        in_stack = False

        for line in lines:
            if 'backtrace' in line.lower() or '#0' in line:
                in_stack = True
            if in_stack:
                if line.strip().startswith('#') or 'at ' in line:
                    stack_lines.append(line)
                elif stack_lines and not line.strip():
                    break

        return '\n'.join(stack_lines) if stack_lines else "No stack trace available"

    def _extract_signal(self, stderr: str) -> str:
        """Extract signal information"""
        for line in stderr.split('\n'):
            if 'signal' in line.lower() or 'SIGSEGV' in line or 'SIGABRT' in line:
                return line.strip()
        return "Unknown signal"

    def _extract_registers(self, stderr: str) -> dict:
        """Extract register dump if available"""
        registers = {}
        for line in stderr.split('\n'):
            if any(reg in line for reg in ['rax', 'rbx', 'rcx', 'rdx', 'rip', 'rsp']):
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.lower() in ['rax:', 'rbx:', 'rcx:', 'rdx:', 'rip:', 'rsp:']:
                        if i + 1 < len(parts):
                            registers[part[:-1].upper()] = parts[i + 1]
        return registers

    def display_crash_summary(self, crashes: list = None):
        """Display crash summary table"""
        if crashes is None:
            crashes = self.crashes

        table = Table(title=f"Crash Summary ({len(crashes)} crashes)", show_header=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("File", style="green", width=25)
        table.add_column("Signal", style="red", width=20)
        table.add_column("Size", justify="right", width=10)
        table.add_column("Has Stack", justify="center", width=10)

        for i, crash in enumerate(crashes, 1):
            table.add_row(
                str(i),
                crash['name'][:22] + "..." if len(crash['name']) > 25 else crash['name'],
                crash.get('signal', 'Unknown')[:18],
                f"{crash['size']:,}",
                "✓" if crash.get('stack_trace') else "✗"
            )

        self.console.print(table)

    def display_detailed_crash(self, crash: dict):
        """Display detailed crash information"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="signal", size=4),
            Layout(name="stack", minimum_size=10),
            Layout(name="registers", size=8) if crash.get('registers') else Layout(size=0)
        )

        # Header
        header = Panel(
            f"[bold cyan]{crash['name']}[/bold cyan]\n"
            f"Size: {crash['size']:,} bytes | Timestamp: {crash['timestamp']:.0f}",
            title="Crash Details",
            border_style="cyan"
        )
        layout["header"].update(header)

        # Signal
        signal_text = Text(crash.get('signal', 'Unknown signal'), style="bold red")
        layout["signal"].update(Panel(signal_text, title="Signal", border_style="red"))

        # Stack trace
        stack = crash.get('stack_trace', 'No stack trace available')
        syntax = Syntax(stack, "text", theme="monokai", line_numbers=True)
        layout["stack"].update(Panel(syntax, title="Stack Trace", border_style="yellow"))

        # Registers
        if crash.get('registers'):
            reg_table = Table(show_header=False)
            reg_table.add_column("Register", style="cyan")
            reg_table.add_column("Value", style="green")

            for reg, value in crash['registers'].items():
                reg_table.add_row(reg, value)

            layout["registers"].update(Panel(reg_table, title="Registers", border_style="magenta"))

        self.console.print(layout)

    def compare_crashes(self, crash1: dict, crash2: dict):
        """Compare two crashes side by side"""
        table = Table(title="Crash Comparison", show_header=True)
        table.add_column("Attribute", style="cyan", width=15)
        table.add_column("Crash 1", style="green", width=35)
        table.add_column("Crash 2", style="yellow", width=35)

        table.add_row("File", crash1['name'], crash2['name'])
        table.add_row("Signal", crash1.get('signal', 'Unknown'), crash2.get('signal', 'Unknown'))
        table.add_row("Size", f"{crash1['size']:,} bytes", f"{crash2['size']:,} bytes")
        table.add_row(
            "Stack Trace",
            "Available" if crash1.get('stack_trace') else "N/A",
            "Available" if crash2.get('stack_trace') else "N/A"
        )

        self.console.print(table)

        # Show if they're likely duplicates
        similarity = self._calculate_similarity(crash1, crash2)
        if similarity > 0.8:
            self.console.print(f"\n[yellow]⚠ High similarity ({similarity:.0%}) - likely duplicates[/yellow]")
        else:
            self.console.print(f"\n[green]Similarity: {similarity:.0%}[/green]")

    def _calculate_similarity(self, crash1: dict, crash2: dict) -> float:
        """Calculate crash similarity score"""
        score = 0.0

        # Signal match
        if crash1.get('signal') == crash2.get('signal'):
            score += 0.4

        # Stack trace similarity (simple check)
        stack1 = crash1.get('stack_trace', '')
        stack2 = crash2.get('stack_trace', '')
        if stack1 and stack2:
            common = len(set(stack1.split()) & set(stack2.split()))
            total = len(set(stack1.split()) | set(stack2.split()))
            if total > 0:
                score += 0.6 * (common / total)

        return score

    def filter_crashes(self, crashes: list, signal=None, has_stack=None, min_size=None, max_size=None):
        """Filter crashes by criteria"""
        filtered = crashes

        if signal:
            filtered = [c for c in filtered if signal.lower() in c.get('signal', '').lower()]

        if has_stack is not None:
            filtered = [c for c in filtered if bool(c.get('stack_trace')) == has_stack]

        if min_size is not None:
            filtered = [c for c in filtered if c['size'] >= min_size]

        if max_size is not None:
            filtered = [c for c in filtered if c['size'] <= max_size]

        return filtered

    def sort_crashes(self, crashes: list, by='timestamp', reverse=False):
        """Sort crashes by attribute"""
        if by == 'size':
            return sorted(crashes, key=lambda c: c['size'], reverse=reverse)
        elif by == 'name':
            return sorted(crashes, key=lambda c: c['name'], reverse=reverse)
        else:  # timestamp
            return sorted(crashes, key=lambda c: c['timestamp'], reverse=reverse)

    def interactive_viewer(self):
        """Interactive crash viewer with navigation"""
        self.load_crashes()

        if not self.crashes:
            self.console.print("[yellow]No crashes found[/yellow]")
            return

        self.console.print(Panel.fit(
            "[bold cyan]Interactive Crash Viewer[/bold cyan]\n"
            "Navigate crashes, view details, and compare",
            border_style="cyan"
        ))

        while True:
            self.console.print("\n")
            self.display_crash_summary()

            self.console.print("\n[dim]Commands: [1-N] view crash, [c] compare, [f] filter, [s] sort, [q] quit[/dim]")
            choice = Prompt.ask("Select", default="q")

            if choice.lower() == 'q':
                break
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(self.crashes):
                    self.console.clear()
                    self.display_detailed_crash(self.crashes[idx])
                    Prompt.ask("\nPress Enter to continue")
                    self.console.clear()
            elif choice.lower() == 'c':
                idx1 = int(Prompt.ask("First crash #")) - 1
                idx2 = int(Prompt.ask("Second crash #")) - 1
                if 0 <= idx1 < len(self.crashes) and 0 <= idx2 < len(self.crashes):
                    self.console.clear()
                    self.compare_crashes(self.crashes[idx1], self.crashes[idx2])
                    Prompt.ask("\nPress Enter to continue")
                    self.console.clear()
