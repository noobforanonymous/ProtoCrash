"""Main fuzzing coordinator integrating all components"""

import logging
import signal
import sys
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

from protocrash.fuzzing_engine.corpus import CorpusManager
from protocrash.fuzzing_engine.scheduler import QueueScheduler
from protocrash.fuzzing_engine.stats import FuzzingStats
from protocrash.mutators.mutation_engine import MutationEngine, MutationConfig
from protocrash.monitors.coverage import CoverageTracker
from protocrash.monitors.crash_detector import CrashDetector
from protocrash.monitors.crash_reporter import CrashReporter
from protocrash.core.types import CrashInfo


@dataclass
class FuzzingConfig:
    """Configuration for fuzzing coordinator"""
    target_cmd: List[str]
    corpus_dir: str
    crashes_dir: str
    timeout_ms: int = 5000
    max_iterations: Optional[int] = None  # None = infinite
    stats_interval: int = 10  # Display stats every N seconds


class FuzzingCoordinator:
    """Main fuzzing loop coordinating all components"""

    def __init__(self, config: FuzzingConfig):
        """
        Initialize fuzzing coordinator

        Args:
            config: Fuzzing configuration
        """
        self.config = config
        self.running = False
        self.iteration = 0

        # Initialize components
        self.corpus = CorpusManager(config.corpus_dir)
        self.scheduler = QueueScheduler()
        self.stats = FuzzingStats()
        self.mutation_engine = MutationEngine(MutationConfig())
        self.coverage_tracker = CoverageTracker()
        self.crash_detector = CrashDetector(timeout_ms=config.timeout_ms)
        self.crash_reporter = CrashReporter(output_dir=config.crashes_dir)

        # Track crashes to avoid duplicates
        self.seen_crashes = set()

        # Initialize scheduler with existing corpus entries
        for entry in self.corpus.entries.values():
            self.scheduler.add_input(
                entry.input_hash,
                entry.size,
                entry.coverage_edges,
                entry.execution_count
            )

        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def add_seed(self, seed_data: bytes) -> None:
        """
        Add initial seed to corpus

        Args:
            seed_data: Seed input data
        """
        input_hash = self.corpus.add_input(seed_data)
        self.scheduler.add_input(input_hash, len(seed_data), 0)

    def run(self) -> None:
        """
        Main fuzzing loop
        """
        if self.corpus.get_size() == 0:
            raise ValueError("Corpus is empty - add seeds before fuzzing")

        self.running = True
        logger.info("Starting fuzzing campaign...")
        logger.info("Target: %s", ' '.join(self.config.target_cmd))
        logger.info("Corpus: %d seeds", self.corpus.get_size())

        last_stats_time = 0

        try:
            while self.running:
                # Check max iterations
                if self.config.max_iterations and self.iteration >= self.config.max_iterations:
                    break

                # Get input to fuzz
                input_hash = self._select_input()
                if not input_hash:
                    break

                input_data = self.corpus.get_input(input_hash)
                if not input_data:
                    continue

                # Mutate input
                mutated = self.mutation_engine.mutate(input_data)

                # Execute target with mutated input
                self.coverage_tracker.start_run()
                crash_info = self.crash_detector.execute_and_detect(
                    self.config.target_cmd,
                    mutated
                )

                # Track coverage (simulate - real implementation would use instrumentation)
                # For now, we just check if execution succeeded
                has_new_coverage = False
                if not crash_info.crashed:
                    # In real fuzzer, we'd get coverage bitmap from instrumented target
                    # For now, simulate by checking if we've seen this input
                    has_new_coverage = len(mutated) % 7 == 0  # Placeholder logic

                self.coverage_tracker.end_run()

                # Update stats
                self.stats.increment_execs()

                # Handle crashes
                if crash_info.crashed:
                    self._handle_crash(crash_info, mutated)

                # Handle new coverage
                if has_new_coverage:
                    new_hash = self.corpus.add_input(
                        mutated,
                        coverage_edges=self.coverage_tracker.get_stats().total_edges,
                        found_new_coverage=True
                    )
                    self.scheduler.add_input(
                        new_hash,
                        len(mutated),
                        coverage_contribution=1
                    )

                # Update corpus execution count
                self.corpus.increment_execution_count(input_hash)

                # Update statistics
                self._update_stats()

                # Display stats periodically
                import time
                current_time = time.time()
                if current_time - last_stats_time >= self.config.stats_interval:
                    self._display_stats()
                    last_stats_time = current_time

                self.iteration += 1

        except KeyboardInterrupt:
            logger.warning("Fuzzing interrupted by user")
        finally:
            self._cleanup()

    def _select_input(self) -> Optional[str]:
        """
        Select next input to fuzz

        Returns:
            Input hash or None
        """
        # Try to get from queue first
        input_hash = self.scheduler.get_next()

        # If queue empty, get random from corpus
        if not input_hash:
            random_input = self.corpus.get_random_input()
            if random_input:
                # Add random inputs back to queue
                for hash_val in self.corpus.get_all_hashes():
                    metadata = self.corpus.get_metadata(hash_val)
                    if metadata:
                        self.scheduler.add_input(
                            hash_val,
                            metadata.size,
                            1 if metadata.found_new_coverage else 0,
                            metadata.execution_count
                        )
                input_hash = self.scheduler.get_next()

        return input_hash

    def _handle_crash(self, crash_info: CrashInfo, input_data: bytes) -> None:
        """
        Handle discovered crash

        Args:
            crash_info: Crash information
            input_data: Input that caused crash
        """
        crash_info.input_data = input_data

        # Generate crash ID
        crash_id = self.crash_reporter.classifier.generate_crash_id(crash_info)

        # Check if we've seen this crash before
        if crash_id in self.seen_crashes:
            return

        self.seen_crashes.add(crash_id)

        # Save crash
        self.crash_reporter.save_crash(crash_info, crash_id)

        # Update stats
        if crash_info.crash_type.name == "HANG":
            self.stats.add_hang()
        else:
            self.stats.add_crash()

        logger.warning("New crash found: %s (%s)", crash_id, crash_info.crash_type.name)

    def _update_stats(self) -> None:
        """Update fuzzing statistics"""
        coverage_stats = self.coverage_tracker.get_stats()

        self.stats.update_coverage(
            total_edges=coverage_stats.total_edges,
            max_edges=10000  # Placeholder
        )

        self.stats.update_corpus_stats(
            corpus_size=self.corpus.get_size(),
            queue_depth=self.scheduler.get_size()
        )

    def _display_stats(self) -> None:
        """Display current fuzzing statistics"""
        # Clear screen and display stats
        sys.stdout.write("\033[2J\033[H")
        stats_output = str(self.stats.get_formatted_stats())
        sys.stdout.write(stats_output + "\n")
        sys.stdout.flush()

    def _signal_handler(self, signum, frame) -> None:
        """
        Handle termination signals

        Args:
            signum: Signal number
            frame: Frame object
        """
        logger.info("Received signal %d, shutting down...", signum)
        self.running = False

    def _cleanup(self) -> None:
        """Cleanup and final statistics"""
        logger.info("="*60)
        logger.info("FUZZING CAMPAIGN COMPLETE")
        logger.info("="*60)
        logger.info("\n%s", self.stats.get_formatted_stats())
        logger.info("Results saved to:")
        logger.info("  Corpus: %s", self.config.corpus_dir)
        logger.info("  Crashes: %s", self.config.crashes_dir)
