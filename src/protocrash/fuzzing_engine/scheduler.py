"""Queue scheduling for input prioritization"""
import heapq
from typing import List, Optional
from dataclasses import dataclass
@dataclass
class QueueEntry:
    """Entry in the fuzzing queue"""
    priority: float  # Lower = higher priority
    input_hash: str
    size: int
    execution_count: int
    coverage_contribution: int
    def __lt__(self, other):
        """For heap comparison"""
        return self.priority < other.priority
class QueueScheduler:
    """Prioritize which inputs to fuzz next (AFL-style)"""
    def __init__(self):
        """Initialize queue scheduler"""
        self.queue: List[QueueEntry] = []
        self.in_queue: set = set()
    def add_input(self, input_hash: str, size: int, coverage_contribution: int,
                  execution_count: int = 0) -> None:
        """
        Add input to queue
        Args:
            input_hash: Input hash
            size: Input size in bytes
            coverage_contribution: Number of new edges this input found
            execution_count: How many times this input has been executed
        """
        if input_hash in self.in_queue:
            return
        # Calculate priority (AFL-style scoring)
        priority = self._calculate_priority(
            size, coverage_contribution, execution_count
        )
        entry = QueueEntry(
            priority=priority,
            input_hash=input_hash,
            size=size,
            execution_count=execution_count,
            coverage_contribution=coverage_contribution
        )
        heapq.heappush(self.queue, entry)
        self.in_queue.add(input_hash)
    def get_next(self) -> Optional[str]:
        """
        Get next input to fuzz
        Returns:
            Input hash or None if queue empty
        """
        if not self.queue:
            return None
        entry = heapq.heappop(self.queue)
        self.in_queue.remove(entry.input_hash)
        return entry.input_hash
    def peek_next(self) -> Optional[str]:
        """
        Peek at next input without removing
        Returns:
            Input hash or None if queue empty
        """
        if not self.queue:
            return None
        return self.queue[0].input_hash
    def update_priority(self, input_hash: str, execution_count: int) -> None:
        """
        Update priority for input (called after execution)
        Args:
            input_hash: Input hash
            execution_count: Updated execution count
        """
        # Remove from queue and re-add with updated priority
        # Find and remove entry
        for i, entry in enumerate(self.queue):
            if entry.input_hash == input_hash:
                # Remove from heap
                self.queue[i] = self.queue[-1]
                self.queue.pop()
                if i < len(self.queue):
                    heapq.heapify(self.queue)
                self.in_queue.remove(input_hash)
                # Re-add with updated execution count
                self.add_input(
                    input_hash,
                    entry.size,
                    entry.coverage_contribution,
                    execution_count
                )
                break
    def get_size(self) -> int:
        """
        Get queue size
        Returns:
            Number of inputs in queue
        """
        return len(self.queue)
    def clear(self) -> None:
        """Clear the queue"""
        self.queue.clear()
        self.in_queue.clear()
    def _calculate_priority(self, size: int, coverage_contribution: int,
                           execution_count: int) -> float:
        """
        Calculate priority score (AFL-style)
        Lower score = higher priority
        Args:
            size: Input size
            coverage_contribution: New edges found
            execution_count: Execution count
        Returns:
            Priority score
        """
        # Favor inputs that found new coverage
        coverage_factor = 1.0 / (coverage_contribution + 1)
        # Favor smaller inputs (faster execution)
        size_factor = size / 1024.0  # Normalize to KB
        # Penalize heavily-executed inputs
        exec_factor = execution_count / 10.0
        # Combined priority
        priority = (coverage_factor * 0.5) + (size_factor * 0.3) + (exec_factor * 0.2)
        return priority
    def get_stats(self) -> dict:
        """
        Get queue statistics
        Returns:
            Dictionary of statistics
        """
        if not self.queue:
            return {
                "queue_depth": 0,
                "avg_priority": 0.0,
                "min_priority": 0.0,
                "max_priority": 0.0
            }
        priorities = [entry.priority for entry in self.queue]
        return {
            "queue_depth": len(self.queue),
            "avg_priority": sum(priorities) / len(priorities),
            "min_priority": min(priorities),
            "max_priority": max(priorities)
        }
