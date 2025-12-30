"""
Distributed coordinator for multi-process fuzzing
Master coordinator that spawns and manages multiple
worker processes with corpus synchronization.
"""
import time
import tempfile
import multiprocessing as mp
from typing import List, Optional
from protocrash.fuzzing_engine.coordinator import FuzzingConfig
from protocrash.distributed.worker import FuzzingWorker
from protocrash.distributed.stats_aggregator import StatsAggregator
class DistributedCoordinator:
    """
    Master coordinator for distributed fuzzing
    Spawns multiple worker processes, manages corpus
    synchronization, and aggregates statistics.
    """
    def __init__(
        self,
        config: FuzzingConfig,
        num_workers: Optional[int] = None,
        sync_interval: float = 5.0
    ):
        """
        Initialize distributed coordinator
        Args:
            config: Fuzzing configuration
            num_workers: Number of workers (default: CPU count)
            sync_interval: Corpus sync interval in seconds
        """
        self.config = config
        self.num_workers = num_workers or mp.cpu_count()
        self.sync_interval = sync_interval
        # Create temporary sync directory
        self.sync_dir = tempfile.mkdtemp(prefix="protocrash_sync_")
        # Stats queue for worker reporting
        self.stats_queue = mp.Queue()
        # Stats aggregator
        self.aggregator = StatsAggregator(self.num_workers)
        # Worker processes
        self.workers: List[mp.Process] = []
        self.running = False
    def add_seed(self, seed_data: bytes):
        """
        Add initial seed to corpus
        Args:
            seed_data: Seed input data
        """
        # Seeds will be added to each worker's coordinator
        # For now, store in config for worker initialization
        pass
    def run(self, duration: Optional[float] = None):
        """
        Run distributed fuzzing campaign
        Args:
            duration: Campaign duration in seconds (None for infinite)
        """
        self.running = True
        start_time = time.time()
        try:
            # Spawn workers
            self._spawn_workers()
            # Monitor and aggregate stats
            while self.running:
                # Collect stats from queue
                self._collect_stats()
                # Display stats periodically
                if int(time.time()) % 10 == 0:
                    self.aggregator.display_stats()
                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    break
                time.sleep(0.1)
        finally:
            self._cleanup()
    def _spawn_workers(self):
        """Spawn worker processes"""
        for worker_id in range(self.num_workers):
            # Create worker
            worker = FuzzingWorker(
                worker_id=worker_id,
                config=self.config,
                sync_dir=self.sync_dir,
                stats_queue=self.stats_queue,
                sync_interval=self.sync_interval
            )
            # Create process
            process = mp.Process(
                target=worker.run,
                args=(self.config.max_iterations,),
                name=f"Worker-{worker_id}"
            )
            process.start()
            self.workers.append(process)
    def _collect_stats(self):
        """Collect statistics from workers"""
        while not self.stats_queue.empty():
            try:
                stats_data = self.stats_queue.get(block=False)
                worker_id = stats_data['worker_id']
                stats = stats_data['stats']
                self.aggregator.update_worker_stats(worker_id, stats)
            except:
                break
    def _cleanup(self):
        """Cleanup and shutdown workers"""
        self.running = False
        # Terminate workers
        for process in self.workers:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5.0)
                # Force kill if still alive
                if process.is_alive():
                    process.kill()
                    process.join()
        # Final stats collection
        self._collect_stats()
        # Display final stats
        self.aggregator.display_stats()
        # Cleanup sync directory
        try:
            import shutil
            shutil.rmtree(self.sync_dir)
        except:
            pass
