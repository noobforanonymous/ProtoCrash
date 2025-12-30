"""Fuzzing statistics tracking"""

import time
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class FuzzingStats:
    """Track fuzzing statistics"""

    # Execution stats
    total_execs: int = 0
    unique_crashes: int = 0
    unique_hangs: int = 0

    # Coverage stats
    total_edges: int = 0
    coverage_percent: float = 0.0

    # Corpus stats
    corpus_size: int = 0
    queue_depth: int = 0

    # Performance stats
    execs_per_sec: float = 0.0
    time_elapsed: float = 0.0

    # Timestamp
    start_time: float = 0.0
    last_update: float = 0.0

    def __post_init__(self):
        """Initialize timestamps"""
        if self.start_time == 0.0:
            self.start_time = time.time()
        if self.last_update == 0.0:
            self.last_update = time.time()

    def increment_execs(self, count: int = 1) -> None:
        """
        Increment execution count

        Args:
            count: Number to increment by
        """
        self.total_execs += count
        self._update_performance()

    def add_crash(self) -> None:
        """Record new unique crash"""
        self.unique_crashes += 1

    def add_hang(self) -> None:
        """Record new unique hang"""
        self.unique_hangs += 1

    def update_coverage(self, total_edges: int, max_edges: int = 10000) -> None:
        """
        Update coverage statistics

        Args:
            total_edges: Total unique edges discovered
            max_edges: Maximum possible edges (estimate)
        """
        self.total_edges = total_edges
        self.coverage_percent = (total_edges / max_edges) * 100.0 if max_edges > 0 else 0.0

    def update_corpus_stats(self, corpus_size: int, queue_depth: int) -> None:
        """
        Update corpus and queue statistics

        Args:
            corpus_size: Current corpus size
            queue_depth: Current queue depth
        """
        self.corpus_size = corpus_size
        self.queue_depth = queue_depth

    def _update_performance(self) -> None:
        """Update performance metrics"""
        self.last_update = time.time()
        self.time_elapsed = self.last_update - self.start_time

        if self.time_elapsed > 0:
            self.execs_per_sec = self.total_execs / self.time_elapsed

    def get_formatted_stats(self) -> str:
        """
        Get formatted statistics string

        Returns:
            Formatted statistics for display
        """
        self._update_performance()

        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    FUZZING STATISTICS                         ║
╠══════════════════════════════════════════════════════════════╣
║ Executions     : {self.total_execs:>10}                              ║
║ Exec/sec       : {self.execs_per_sec:>10.2f}                              ║
║ Time Elapsed   : {self.time_elapsed:>10.2f}s                             ║
║                                                              ║
║ Unique Crashes : {self.unique_crashes:>10}                              ║
║ Unique Hangs   : {self.unique_hangs:>10}                              ║
║                                                              ║
║ Coverage       : {self.coverage_percent:>10.2f}%                            ║
║ Total Edges    : {self.total_edges:>10}                              ║
║                                                              ║
║ Corpus Size    : {self.corpus_size:>10}                              ║
║ Queue Depth    : {self.queue_depth:>10}                              ║
╚══════════════════════════════════════════════════════════════╝
        """.strip()

    def to_dict(self) -> Dict[str, Any]:
        """
        Export stats as dictionary

        Returns:
            Dictionary of all statistics
        """
        self._update_performance()
        return asdict(self)

    def reset(self) -> None:
        """Reset all statistics"""
        self.total_execs = 0
        self.unique_crashes = 0
        self.unique_hangs = 0
        self.total_edges = 0
        self.coverage_percent = 0.0
        self.corpus_size = 0
        self.queue_depth = 0
        self.execs_per_sec = 0.0
        self.time_elapsed = 0.0
        self.start_time = time.time()
        self.last_update = time.time()
