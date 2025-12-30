"""Test queue scheduler"""

import pytest
from protocrash.fuzzing_engine.scheduler import QueueScheduler, QueueEntry


class TestQueueScheduler:
    """Test QueueScheduler class"""

    @pytest.fixture
    def scheduler(self):
        """Create QueueScheduler instance"""
        return QueueScheduler()

    def test_init(self, scheduler):
        """Test initialization"""
        assert scheduler.get_size() == 0

    def test_add_input(self, scheduler):
        """Test adding input"""
        scheduler.add_input("hash1", size=100, coverage_contribution=5)
        assert scheduler.get_size() == 1

    def test_add_duplicate(self, scheduler):
        """Test adding duplicate input"""
        scheduler.add_input("hash1", size=100, coverage_contribution=5)
        scheduler.add_input("hash1", size=100, coverage_contribution=5)
        assert scheduler.get_size() == 1  # No duplicate

    def test_get_next(self, scheduler):
        """Test getting next input"""
        scheduler.add_input("hash1", size=100, coverage_contribution=5)
        
        next_hash = scheduler.get_next()
        assert next_hash == "hash1"
        assert scheduler.get_size() == 0  # Removed from queue

    def test_get_next_empty(self, scheduler):
        """Test getting next from empty queue"""
        result = scheduler.get_next()
        assert result is None

    def test_peek_next(self, scheduler):
        """Test peeking at next input"""
        scheduler.add_input("hash1", size=100, coverage_contribution=5)
        
        peeked = scheduler.peek_next()
        assert peeked == "hash1"
        assert scheduler.get_size() == 1  # Not removed

    def test_peek_next_empty(self, scheduler):
        """Test peeking at empty queue"""
        result = scheduler.peek_next()
        assert result is None

    def test_priority_ordering(self, scheduler):
        """Test inputs are ordered by priority"""
        # Add inputs with different priorities
        # High coverage contribution = high priority (lower score)
        scheduler.add_input("high_priority", size=100, coverage_contribution=10)
        scheduler.add_input("low_priority", size=100, coverage_contribution=0)
        scheduler.add_input("medium_priority", size=100, coverage_contribution=5)
        
        # Should get high priority first
        assert scheduler.get_next() == "high_priority"
        assert scheduler.get_next() == "medium_priority"
        assert scheduler.get_next() == "low_priority"

    def test_size_priority(self, scheduler):
        """Test smaller inputs have higher priority"""
        scheduler.add_input("small", size=50, coverage_contribution=1)
        scheduler.add_input("large", size=500, coverage_contribution=1)
        
        # Smaller should come first
        assert scheduler.get_next() == "small"

    def test_execution_count_penalty(self, scheduler):
        """Test heavily executed inputs have lower priority"""
        scheduler.add_input("fresh", size=100, coverage_contribution=1, execution_count=0)
        scheduler.add_input("executed", size=100, coverage_contribution=1, execution_count=100)
        
        # Fresh should come first
        assert scheduler.get_next() == "fresh"

    def test_update_priority(self, scheduler):
        """Test updating priority"""
        scheduler.add_input("hash1", size=100, coverage_contribution=5, execution_count=0)
        scheduler.add_input("hash2", size=100, coverage_contribution=5, execution_count=0)
        
        # hash1 should be first
        first = scheduler.peek_next()
        
        # Update hash1 to be heavily executed
        scheduler.update_priority("hash1", execution_count=100)
        
        # Now hash2 should be first
        assert scheduler.peek_next() == "hash2"

    def test_clear(self, scheduler):
        """Test clearing queue"""
        scheduler.add_input("hash1", size=100, coverage_contribution=5)
        scheduler.add_input("hash2", size=100, coverage_contribution=5)
        
        assert scheduler.get_size() == 2
        
        scheduler.clear()
        assert scheduler.get_size() == 0

    def test_get_stats(self, scheduler):
        """Test getting statistics"""
        # Empty queue
        stats = scheduler.get_stats()
        assert stats["queue_depth"] == 0
        
        # Add inputs
        scheduler.add_input("hash1", size=100, coverage_contribution=5)
        scheduler.add_input("hash2", size=200, coverage_contribution=10)
        scheduler.add_input("hash3", size=150, coverage_contribution=7)
        
        stats = scheduler.get_stats()
        assert stats["queue_depth"] == 3
        assert "avg_priority" in stats
        assert "min_priority" in stats
        assert "max_priority" in stats
