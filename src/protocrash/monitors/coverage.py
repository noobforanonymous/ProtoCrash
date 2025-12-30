"""Main coverage tracking interface"""

from pathlib import Path
from typing import List

from protocrash.monitors.coverage_map import CoverageMap
from protocrash.monitors.coverage_comparator import CoverageComparator
from protocrash.monitors.coverage_analyzer import CoverageAnalyzer, CoverageStats


class CoverageTracker:
    """Main coverage tracking interface"""

    def __init__(self, shared_memory: bool = False):
        """
        Initialize coverage tracker

        Args:
            shared_memory: Use shared memory for IPC (future enhancement)
        """
        self.coverage_map = CoverageMap(shared_memory)
        self.comparator = CoverageComparator()
        self.analyzer = CoverageAnalyzer()

        # Track coverage history
        self.coverage_history: List[bytearray] = []
        self.run_count = 0

    def start_run(self) -> None:
        """Prepare for new execution"""
        self.coverage_map.reset()
        self.run_count += 1

    def end_run(self) -> bool:
        """
        Complete execution and check for new coverage

        Returns:
            True if new coverage was found
        """
        has_new = self.coverage_map.has_new_coverage()

        if has_new:
            # Save this coverage
            self.coverage_history.append(bytearray(self.coverage_map.bitmap))

            # Mark as seen
            self.coverage_map.update_virgin_map()

        return has_new

    def record_edge(self, current_location: int) -> None:
        """
        Record edge execution

        Args:
            current_location: Current basic block ID
        """
        self.coverage_map.record_edge(current_location)

    def get_coverage_bitmap(self) -> bytearray:
        """Get current coverage bitmap"""
        return bytearray(self.coverage_map.bitmap)

    def get_stats(self) -> CoverageStats:
        """Get coverage statistics"""
        return self.analyzer.analyze(self.coverage_map.bitmap)

    def get_total_edges(self) -> int:
        """Get total unique edges found across all runs"""
        return self.coverage_map.total_edges_found

    def export_coverage(self, filepath: Path) -> None:
        """
        Export coverage map to file

        Args:
            filepath: Path to export coverage bitmap
        """
        filepath.write_bytes(bytes(self.coverage_map.bitmap))

    def import_coverage(self, filepath: Path) -> None:
        """
        Import coverage map from file

        Args:
            filepath: Path to coverage bitmap file
        """
        data = filepath.read_bytes()
        if len(data) == CoverageMap.MAP_SIZE:
            self.coverage_map.bitmap = bytearray(data)
        else:
            raise ValueError(f"Invalid coverage file size: {len(data)}, expected {CoverageMap.MAP_SIZE}")
