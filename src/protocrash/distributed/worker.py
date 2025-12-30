"""
Fuzzing worker process for distributed fuzzing

Individual worker process that runs independent fuzzing loop
with periodic corpus synchronization.
"""

import time
import signal
from typing import Optional
from multiprocessing import Queue

from protocrash.fuzzing_engine.coordinator import FuzzingCoordinator, FuzzingConfig
from protocrash.distributed.corpus_sync import CorpusSynchronizer


class FuzzingWorker:
    """
    Individual fuzzing worker process

    Runs independent fuzzing loop with local corpus and
    periodic synchronization with other workers.
    """

    def __init__(
        self,
        worker_id: int,
        config: FuzzingConfig,
        sync_dir: str,
        stats_queue: Queue,
        sync_interval: float = 5.0
    ):
        """
        Initialize fuzzing worker

        Args:
            worker_id: Unique worker identifier
            config: Fuzzing configuration
            sync_dir: Shared synchronization directory
            stats_queue: Queue for stats reporting to master
            sync_interval: Seconds between corpus syncs
        """
        self.worker_id = worker_id
        self.config = config
        self.sync_dir = sync_dir
        self.stats_queue = stats_queue
        self.sync_interval = sync_interval

        # Create local coordinator
        self.coordinator = FuzzingCoordinator(config)

        # Create corpus synchronizer
        self.synchronizer = CorpusSynchronizer(sync_dir, worker_id)

        # Track sync timing
        self.last_sync_time = 0.0
        self.running = False

    def run(self, max_iterations: Optional[int] = None):
        """
        Run fuzzing loop with periodic synchronization

        Args:
            max_iterations: Maximum iterations (None for infinite)
        """
        self.running = True
        iteration = 0

        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            while self.running:
                # Run one fuzzing iteration
                self._fuzzing_iteration()
                iteration += 1

                # Check sync interval
                if time.time() - self.last_sync_time >= self.sync_interval:
                    self._sync_corpus()
                    self._report_stats()
                    self.last_sync_time = time.time()

                # Check max iterations
                if max_iterations and iteration >= max_iterations:
                    break

        finally:
            self._cleanup()

    def _fuzzing_iteration(self):
        """Execute single fuzzing iteration"""
        # Select input from corpus
        input_hash = self.coordinator._select_input()
        if not input_hash:
            return

        # Get input data
        input_data = self.coordinator.corpus.get_input(input_hash)
        if not input_data:
            return

        # Mutate input
        mutated = self.coordinator.mutation_engine.mutate(input_data)

        # Execute and detect crashes
        crash_info = self.coordinator.crash_detector.execute_and_detect(
            self.coordinator.config.target_cmd,
            mutated
        )

        # Update stats
        self.coordinator.stats.record_execution()

        # Handle crashes
        if crash_info.crashed:
            self.coordinator._handle_crash(crash_info, mutated)

        # Check for new coverage
        # (Simplified - real implementation would check coverage map)

    def _sync_corpus(self):
        """Synchronize corpus with other workers"""
        # Import new inputs from other workers
        new_inputs = self.synchronizer.import_new_inputs()

        for synced_input in new_inputs:
            # Add to local corpus if new coverage
            self.coordinator.corpus.add_input(
                synced_input.input_data,
                coverage_hash=synced_input.coverage_hash
            )

        # Export interesting local inputs
        # (Simplified - would export based on coverage gains)

    def _report_stats(self):
        """Report statistics to master via queue"""
        try:
            self.stats_queue.put({
                'worker_id': self.worker_id,
                'stats': self.coordinator.stats,
                'timestamp': time.time()
            }, block=False)
        except:
            # Queue full, skip this report
            pass

    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        self.running = False

    def _cleanup(self):
        """Cleanup resources"""
        # Report final stats
        self._report_stats()

        # Cleanup synchronizer
        self.synchronizer.cleanup()
