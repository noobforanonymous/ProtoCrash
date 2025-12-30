"""Distributed fuzzing module for multi-core parallel execution"""

from protocrash.distributed.corpus_sync import CorpusSynchronizer
from protocrash.distributed.worker import FuzzingWorker
from protocrash.distributed.stats_aggregator import StatsAggregator
from protocrash.distributed.coordinator import DistributedCoordinator

__all__ = [
    'CorpusSynchronizer',
    'FuzzingWorker',
    'StatsAggregator',
    'DistributedCoordinator',
]
