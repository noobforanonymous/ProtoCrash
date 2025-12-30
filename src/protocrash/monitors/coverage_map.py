"""Coverage tracking implementation (AFL-style)"""



class CoverageMap:
    """AFL-style 64KB coverage bitmap"""

    MAP_SIZE = 65536  # 64KB

    def __init__(self, shared_memory: bool = False):
        """
        Initialize coverage map

        Args:
            shared_memory: Use shared memory for IPC with target (future enhancement)
        """
        self.bitmap = bytearray(self.MAP_SIZE)

        # Virgin map tracks unseen edges (0xFF = unseen, 0x00 = seen)
        self.virgin_map = bytearray([0xFF] * self.MAP_SIZE)

        # Track previous location for edge calculation
        self.prev_location = 0

        # Statistics
        self.total_edges_found = 0
        self.edges_in_last_run = 0

    def reset(self) -> None:
        """Clear bitmap for new execution"""
        for i in range(self.MAP_SIZE):
            self.bitmap[i] = 0
        self.prev_location = 0
        self.edges_in_last_run = 0

    def record_edge(self, current_location: int) -> None:
        """
        Record edge execution (AFL-style)

        This is called from instrumented target code

        Args:
            current_location: Random ID assigned to current basic block
        """
        # Calculate edge ID via XOR
        edge_id = current_location ^ self.prev_location

        # Hash to bitmap index
        index = edge_id % self.MAP_SIZE

        # Increment hit counter (with saturation at 255)
        if self.bitmap[index] < 255:
            self.bitmap[index] += 1

        # Update previous location for next edge
        # Right shift to avoid reversing A->B to B->A
        self.prev_location = current_location >> 1

    def has_new_coverage(self) -> bool:
        """
        Check if current execution found new coverage

        Returns:
            True if new edges or hit count buckets discovered
        """
        found_new = False

        for i in range(self.MAP_SIZE):
            if self.bitmap[i]:
                # Classify hit count into bucket
                classified = self._count_class(self.bitmap[i])

                # Check if this bucket was virgin
                if self.virgin_map[i] & classified:
                    found_new = True
                    self.edges_in_last_run += 1

        return found_new

    def update_virgin_map(self) -> None:
        """Mark current coverage as seen"""
        for i in range(self.MAP_SIZE):
            if self.bitmap[i]:
                # Classify and mark as seen
                classified = self._count_class(self.bitmap[i])
                self.virgin_map[i] &= ~classified

        self.total_edges_found += self.edges_in_last_run

    def get_edge_count(self) -> int:
        """Count unique edges hit in current execution"""
        count = 0
        for byte_val in self.bitmap:
            if byte_val > 0:
                count += 1
        return count

    def classify_counts(self) -> bytearray:
        """
        Classify hit counts into buckets (AFL-style)

        Returns:
            Classified bitmap with bucketed hit counts
        """
        classified = bytearray(self.MAP_SIZE)

        for i in range(self.MAP_SIZE):
            classified[i] = self._count_class(self.bitmap[i])

        return classified

    def _count_class(self, count: int) -> int:
        """
        Classify hit count into bucket

        Buckets: 0, 1, 2, 3, 4-7, 8-15, 16-31, 32-127, 128+

        Returns:
            Bucket identifier (bit pattern)
        """
        if count == 0:
            return 0
        elif count == 1:
            return 1
        elif count == 2:
            return 2
        elif count == 3:
            return 4
        elif count <= 7:
            return 8
        elif count <= 15:
            return 16
        elif count <= 31:
            return 32
        elif count <= 127:
            return 64
        else:
            return 128
