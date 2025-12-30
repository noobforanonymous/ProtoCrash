"""
Statistics aggregation for distributed fuzzing
Collects and aggregates statistics from multiple worker processes
to provide global campaign visibility.
"""
import logging
import time
from typing import Dict, List
from dataclasses import dataclass, field
from protocrash.fuzzing_engine.stats import FuzzingStats
logger = logging.getLogger(__name__)
@dataclass
class WorkerStats:
    """Statistics for a single worker"""
    worker_id: int
    executions: int = 0
    crashes: int = 0
    hangs: int = 0
    timeouts: int = 0
    corpus_size: int = 0
    coverage_edges: int = 0
    last_update: float = field(default_factory=time.time)
    start_time: float = field(default_factory=time.time)
    def get_exec_per_sec(self) -> float:
        """Calculate executions per second for this worker"""
        elapsed = time.time() - self.start_time
        if elapsed <= 0:
            return 0.0
        return self.executions / elapsed
class StatsAggregator:
    """
    Aggregates statistics from multiple worker processes
    Provides global campaign metrics by combining individual
    worker statistics and calculating aggregate rates.
    """
    def __init__(self, num_workers: int):
        """
        Initialize statistics aggregator
        Args:
            num_workers: Total number of worker processes
        """
        self.num_workers = num_workers
        self.worker_stats: Dict[int, WorkerStats] = {}
        self.start_time = time.time()
        # Initialize stats for all workers
        for worker_id in range(num_workers):
            self.worker_stats[worker_id] = WorkerStats(worker_id=worker_id)
    def update_worker_stats(self, worker_id: int, stats: FuzzingStats):
        """
        Update statistics for a specific worker
        Args:
            worker_id: Worker identifier
            stats: FuzzingStats object from worker
        """
        if worker_id not in self.worker_stats:
            self.worker_stats[worker_id] = WorkerStats(worker_id=worker_id)
        worker = self.worker_stats[worker_id]
        worker.executions = stats.total_execs
        worker.crashes = stats.unique_crashes
        worker.hangs = stats.unique_hangs
        worker.timeouts = stats.timeouts
        worker.corpus_size = stats.corpus_size
        worker.coverage_edges = stats.coverage_edges
        worker.last_update = time.time()
    def get_aggregate_stats(self) -> Dict:
        """
        Get aggregated statistics across all workers
        Returns:
            Dict with global campaign metrics
        """
        total_execs = sum(w.executions for w in self.worker_stats.values())
        total_crashes = sum(w.crashes for w in self.worker_stats.values())
        total_hangs = sum(w.hangs for w in self.worker_stats.values())
        total_timeouts = sum(w.timeouts for w in self.worker_stats.values())
        total_corpus = sum(w.corpus_size for w in self.worker_stats.values())
        total_coverage = max(w.coverage_edges for w in self.worker_stats.values()) if self.worker_stats else 0
        # Calculate global exec/sec
        elapsed = time.time() - self.start_time
        global_exec_per_sec = total_execs / elapsed if elapsed > 0 else 0.0
        return {
            'total_executions': total_execs,
            'total_crashes': total_crashes,
            'total_hangs': total_hangs,
            'total_timeouts': total_timeouts,
            'total_corpus_size': total_corpus,
            'coverage_edges': total_coverage,
            'global_exec_per_sec': global_exec_per_sec,
            'num_workers': len(self.worker_stats),
            'elapsed_time': elapsed
        }
    def get_worker_breakdown(self) -> List[Dict]:
        """
        Get per-worker statistics breakdown
        Returns:
            List of dicts with per-worker metrics
        """
        breakdown = []
        for worker in sorted(self.worker_stats.values(), key=lambda w: w.worker_id):
            breakdown.append({
                'worker_id': worker.worker_id,
                'executions': worker.executions,
                'crashes': worker.crashes,
                'hangs': worker.hangs,
                'corpus_size': worker.corpus_size,
                'exec_per_sec': worker.get_exec_per_sec(),
                'last_update': worker.last_update
            })
        return breakdown
    def display_stats(self):
        """Display formatted statistics to console"""
        agg = self.get_aggregate_stats()
        logger.info("=" * 60)
        logger.info("DISTRIBUTED FUZZING STATISTICS")
        logger.info("=" * 60)
        logger.info("Workers:         %d", agg['num_workers'])
        logger.info("Elapsed Time:    %.1fs", agg['elapsed_time'])
        logger.info("Total Execs:     %s", f"{agg['total_executions']:,}")
        logger.info("Exec/sec:        %.1f", agg['global_exec_per_sec'])
        logger.info("Unique Crashes:  %d", agg['total_crashes'])
        logger.info("Unique Hangs:    %d", agg['total_hangs'])
        logger.info("Corpus Size:     %d", agg['total_corpus_size'])
        logger.info("Coverage Edges:  %d", agg['coverage_edges'])
        logger.info("=" * 60)
        # Per-worker breakdown
        logger.info("PER-WORKER BREAKDOWN:")
        logger.info("-" * 60)
        for w in self.get_worker_breakdown():
            logger.info("Worker %d: %s execs (%.1f/s), %d crashes, %d hangs",
                       w['worker_id'], f"{w['executions']:,}",
                       w['exec_per_sec'], w['crashes'], w['hangs'])
        logger.info("-" * 60)
    def get_inactive_workers(self, timeout: float = 10.0) -> List[int]:
        """
        Get list of workers that haven't reported recently
        Args:
            timeout: Seconds since last update to consider inactive
        Returns:
            List of inactive worker IDs
        """
        current_time = time.time()
        inactive = []
        for worker in self.worker_stats.values():
            if current_time - worker.last_update > timeout:
                inactive.append(worker.worker_id)
        return inactive
    def reset_stats(self):
        """Reset all statistics to zero"""
        for worker in self.worker_stats.values():
            worker.executions = 0
            worker.crashes = 0
            worker.hangs = 0
            worker.timeouts = 0
            worker.corpus_size = 0
            worker.coverage_edges = 0
            worker.start_time = time.time()
        self.start_time = time.time()
