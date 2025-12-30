"""Coverage analysis and statistics"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CoverageStats:
    """Statistics about coverage"""
    total_edges: int
    unique_edges: int
    edge_density: float  # % of bitmap used
    max_hit_count: int
    avg_hit_count: float
    hot_edges: List[int]  # Most frequently hit edges


class CoverageAnalyzer:
    """Analyze coverage patterns"""

    def analyze(self, bitmap: bytearray) -> CoverageStats:
        """
        Generate statistics from coverage bitmap

        Args:
            bitmap: Coverage bitmap to analyze

        Returns:
            CoverageStats with analysis results
        """
        total_edges = 0
        unique_edges = 0
        max_hit = 0
        sum_hits = 0
        hot_edges = []

        for i, count in enumerate(bitmap):
            if count > 0:
                unique_edges += 1
                total_edges += count
                sum_hits += count
                max_hit = max(max_hit, count)

                # Track hot edges (hit > 100 times)
                if count > 100:
                    hot_edges.append(i)

        edge_density = (unique_edges / len(bitmap)) * 100 if len(bitmap) > 0 else 0.0
        avg_hit = sum_hits / unique_edges if unique_edges > 0 else 0.0

        return CoverageStats(
            total_edges=total_edges,
            unique_edges=unique_edges,
            edge_density=edge_density,
            max_hit_count=max_hit,
            avg_hit_count=avg_hit,
            hot_edges=hot_edges
        )

    def identify_interesting_inputs(
        self, corpus_coverage: Dict[str, bytearray], map_size: int = 65536
    ) -> List[str]:
        """
        Identify corpus inputs that provide unique coverage

        Args:
            corpus_coverage: Map of input_id -> coverage_bitmap
            map_size: Size of coverage bitmap

        Returns:
            List of interesting input IDs
        """
        virgin = bytearray([0xFF] * map_size)
        interesting = []

        for input_id, bitmap in corpus_coverage.items():
            # Check if this input provides new coverage
            has_new = False
            for i in range(min(len(bitmap), len(virgin))):
                if bitmap[i] and (bitmap[i] & virgin[i]):
                    has_new = True
                    break

            if has_new:
                interesting.append(input_id)
                # Update virgin map
                for i in range(min(len(bitmap), len(virgin))):
                    if bitmap[i]:
                        virgin[i] &= ~bitmap[i]

        return interesting
