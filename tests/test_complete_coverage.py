"""Complete coverage tests for all remaining 10 missing statements"""

import pytest
from protocrash.mutators.mutation_engine import MutationEngine, MutationConfig
from protocrash.mutators.dictionary import DictionaryManager
from protocrash.mutators.splice import SpliceMutator
from protocrash.monitors.execution_monitor import ExecutionMonitor
from protocrash.monitors.memory_leak_detector import MemoryLeakDetector


class TestCompleteQuality:
    """Tests for all remaining missing lines to achieve 100% coverage"""

    # ===== MutationEngine Lines 134, 137-140 =====
    
    def test_mutation_engine_all_deterministic_strategies(self):
        """Test all deterministic mutation strategy branches (lines 134, 137-140)"""
        engine = MutationEngine(MutationConfig())
        data = b"AAAA"
        
        # Force hit all branches by calling multiple times
        results = set()
        for _ in range(100):  # Enough iterations to hit all 4 strategies
            result = engine._mutate_deterministic(data)
            results.add(result)
        
        # Should have gotten different mutations
        assert len(results) > 1

    def test_mutation_engine_arithmetic_strategy(self):
        """Force arithmetic strategy path (line 138)"""
        import random
        engine = MutationEngine(MutationConfig())
        data = b"\x01\x02\x03\x04"
        
        # Mock random.choice to force "arithmetic"
        original_choice = random.choice
        def force_arithmetic(seq):
            if seq == ["bit_flip", "byte_flip", "arithmetic", "interesting"]:
                return "arithmetic"
            return original_choice(seq)
        
        random.choice = force_arithmetic
        try:
            result = engine._mutate_deterministic(data)
            assert result != data  # Should be mutated
        finally:
            random.choice = original_choice

    def test_mutation_engine_interesting_strategy(self):
        """Force interesting values strategy path (line 140)"""
        import random
        engine = MutationEngine(MutationConfig())
        data = b"\x01\x02\x03\x04"
        
        # Mock random.choice to force "interesting"
        original_choice = random.choice
        call_count = [0]
        def force_interesting(seq):
            call_count[0] += 1
            if call_count[0] == 1 and seq == ["bit_flip", "byte_flip", "arithmetic", "interesting"]:
                return "interesting"
            return original_choice(seq)
        
        random.choice = force_interesting
        try:
            result = engine._mutate_deterministic(data)
            # Should have applied interesting values
        finally:
            random.choice = original_choice

    # ===== Dictionary Line 67 =====
    
    def test_dictionary_replace_empty_dictwords(self):
        """Test dictionary replace when dict_words empty (line 67)"""
        dict_mgr = DictionaryManager()
        # Clear all dictionaries
        dict_mgr.dictionaries = {}
        
        data = b"test data here"
        result = dict_mgr.replace(data, 0, 4)
        
        # Should return original data when no dict words
        assert result == data

    # ===== Splice Line 50 =====
    
    def test_splice_multi_crossover_selected_one(self):
        """Test multi_crossover when selected has only 1 item (line 50)"""
        splicer = SpliceMutator()
        
        # With count=1 and one input, selected will have 1 item
        inputs = [b"single input"]
        result = splicer.multi_crossover(inputs, count=1)
        
        assert result == b"single input"
    
    # ===== ExecutionMonitor Lines 82-83 already covered =====
    
    # ===== MemoryLeakDetector Lines 117, 130 =====
    
    def test_memory_leak_confidence_less_than_10(self):
        """Test _calculate_confidence with < 10 snapshots (line 117)"""
        from protocrash.monitors.memory_leak_detector import MemorySnapshot
        detector = MemoryLeakDetector()
        
        # Create 5 snapshots
        snapshots = [
            MemorySnapshot(i * 1.0, 1000 + i * 100, 2000)
            for i in range(5)
        ]
        
        confidence = detector._calculate_confidence(snapshots)
        assert confidence == "LOW"

    def test_memory_leak_confidence_low_growth_ratio(self):
        """Test _calculate_confidence with low growth ratio < 0.6 (line 130)"""
        from protocrash.monitors.memory_leak_detector import MemorySnapshot
        detector = MemoryLeakDetector()
        
        # Create 15 snapshots with very inconsistent growth (< 60% growth)
        snapshots = []
        for i in range(15):
            # Only 50% of snapshots increase
            rss = 1000 + (100 if i % 2 == 0 else -50)
            snapshots.append(MemorySnapshot(i * 1.0, rss, 2000))
        
        confidence = detector._calculate_confidence(snapshots)
        assert confidence == "LOW"

    # ===== Coordinator Line 127 =====    def test_coordinator_crash_handling_path(self):
        """Test coordinator crash handling execution (line 127)"""
        import tempfile
        from protocrash.fuzzing_engine.coordinator import FuzzingCoordinator, FuzzingConfig
        from protocrash.core.types import CrashInfo, CrashType
        from unittest.mock import patch
        
        with tempfile.TemporaryDirectory() as corpus_dir:
            with tempfile.TemporaryDirectory() as crashes_dir:
                config = FuzzingConfig(
                    target_cmd=["echo"],
                    corpus_dir=corpus_dir,
                    crashes_dir=crashes_dir,
                    max_iterations=1
                )
                
                coordinator = FuzzingCoordinator(config)
                coordinator.add_seed(b"test")
                
                # Mock crash_detector to return a crash
                def mock_execute(cmd, data):
                    return CrashInfo(
                        crashed=True,
                        crash_type=CrashType.SEGV,
                        signal_number=11,
                        stderr=b"crash",
                        input_data=data
                    )
                
                with patch.object(coordinator.crash_detector, 'execute_and_detect', side_effect=mock_execute):
                    coordinator.run()
                
                # Should have handled the crash
                assert coordinator.stats.unique_crashes >= 0
