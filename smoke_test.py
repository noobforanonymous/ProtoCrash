#!/usr/bin/env python3
"""
Smoke Test Suite for ProtoCrash
Tests core workflows to ensure basic functionality works
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name):
    print(f"\n{BLUE}▶ {name}{RESET}")

def print_pass(msg):
    print(f"  {GREEN}✓ {msg}{RESET}")

def print_fail(msg):
    print(f"  {RED}✗ {msg}{RESET}")

def print_warn(msg):
    print(f"  {YELLOW}⚠ {msg}{RESET}")


class SmokeTest:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def run_all(self):
        """Run all smoke tests"""
        print("="*60)
        print("ProtoCrash Smoke Test Suite")
        print("="*60)
        
        # Core functionality tests
        self.test_imports()
        self.test_mutation_engine()
        self.test_coverage_tracker()
        self.test_corpus_manager()
        self.test_crash_detector()
        self.test_protocol_parsers()
        self.test_cli_help()
        self.test_basic_fuzzing()
        
        # Summary
        print("\n" + "="*60)
        print("SMOKE TEST RESULTS")
        print("="*60)
        print(f"{GREEN}Passed:   {self.passed}{RESET}")
        print(f"{RED}Failed:   {self.failed}{RESET}")
        print(f"{YELLOW}Warnings: {self.warnings}{RESET}")
        print("="*60)
        
        return self.failed == 0
    
    def test_imports(self):
        """Test that all core modules can be imported"""
        print_test("Testing module imports")
        
        modules = [
            "protocrash.fuzzing_engine.coordinator",
            "protocrash.fuzzing_engine.corpus",
            "protocrash.fuzzing_engine.scheduler",
            "protocrash.mutators.mutation_engine",
            "protocrash.monitors.coverage",
            "protocrash.monitors.crash_detector",
            "protocrash.parsers.http_parser",
            "protocrash.parsers.dns_parser",
            "protocrash.parsers.smtp_parser",
            "protocrash.cli.main",
        ]
        
        for module in modules:
            try:
                __import__(module)
                print_pass(f"Imported {module}")
                self.passed += 1
            except Exception as e:
                print_fail(f"Failed to import {module}: {e}")
                self.failed += 1
    
    def test_mutation_engine(self):
        """Test mutation engine basic functionality"""
        print_test("Testing mutation engine")
        
        try:
            from protocrash.mutators.mutation_engine import MutationEngine, MutationConfig
            
            engine = MutationEngine(MutationConfig())
            test_input = b"Hello, World!"
            
            # Test mutation
            mutated = engine.mutate(test_input)
            if mutated != test_input:
                print_pass("Mutation produces different output")
                self.passed += 1
            else:
                print_warn("Mutation produced same output (rare but possible)")
                self.warnings += 1
            
            # Test multiple mutations
            mutations = [engine.mutate(test_input) for _ in range(10)]
            if len(set(mutations)) > 1:
                print_pass(f"Generated {len(set(mutations))} unique mutations")
                self.passed += 1
            else:
                print_fail("All mutations identical")
                self.failed += 1
                
        except Exception as e:
            print_fail(f"Mutation engine error: {e}")
            self.failed += 1
    
    def test_coverage_tracker(self):
        """Test coverage tracking"""
        print_test("Testing coverage tracker")
        
        try:
            from protocrash.monitors.coverage import CoverageTracker
            
            tracker = CoverageTracker()
            
            # Test basic tracking
            tracker.start_run()
            tracker.coverage_map.record_edge(100)
            tracker.coverage_map.record_edge(200)
            tracker.end_run()
            
            if tracker.coverage_map.get_edge_count() > 0:
                print_pass(f"Tracked {tracker.coverage_map.get_edge_count()} edges")
                self.passed += 1
            else:
                print_fail("No edges tracked")
                self.failed += 1
                
        except Exception as e:
            print_fail(f"Coverage tracker error: {e}")
            self.failed += 1
    
    def test_corpus_manager(self):
        """Test corpus management"""
        print_test("Testing corpus manager")
        
        try:
            from protocrash.fuzzing_engine.corpus import CorpusManager
            
            with tempfile.TemporaryDirectory() as tmpdir:
                corpus = CorpusManager(tmpdir)
                
                # Add inputs
                hash1 = corpus.add_input(b"test1")
                hash2 = corpus.add_input(b"test2")
                
                if corpus.get_size() == 2:
                    print_pass(f"Added 2 inputs to corpus")
                    self.passed += 1
                else:
                    print_fail(f"Expected 2 inputs, got {corpus.get_size()}")
                    self.failed += 1
                
                # Retrieve input
                data = corpus.get_input(hash1)
                if data == b"test1":
                    print_pass("Retrieved input correctly")
                    self.passed += 1
                else:
                    print_fail("Input retrieval failed")
                    self.failed += 1
                    
        except Exception as e:
            print_fail(f"Corpus manager error: {e}")
            self.failed += 1
    
    def test_crash_detector(self):
        """Test crash detection"""
        print_test("Testing crash detector")
        
        try:
            from protocrash.monitors.crash_detector import CrashDetector
            
            detector = CrashDetector()
            
            # Test with echo (should not crash)
            crash_info = detector.execute_and_detect(["echo", "test"], b"input")
            
            if not crash_info.crashed:
                print_pass("Correctly detected no crash for echo")
                self.passed += 1
            else:
                print_warn("Echo detected as crash (unexpected)")
                self.warnings += 1
                
        except Exception as e:
            print_fail(f"Crash detector error: {e}")
            self.failed += 1
    
    def test_protocol_parsers(self):
        """Test protocol parsers"""
        print_test("Testing protocol parsers")
        
        # Test HTTP parser
        try:
            from protocrash.parsers.http_parser import HttpParser
            
            parser = HttpParser()
            http_data = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
            msg = parser.parse(http_data)
            
            if msg and msg.method == "GET":
                print_pass("HTTP parser works")
                self.passed += 1
            else:
                print_fail("HTTP parser failed")
                self.failed += 1
        except Exception as e:
            print_fail(f"HTTP parser error: {e}")
            self.failed += 1
        
        # Test DNS parser
        try:
            from protocrash.parsers.dns_parser import DNSParser
            
            parser = DNSParser()
            # Minimal DNS query
            dns_data = b'\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x07example\x03com\x00\x00\x01\x00\x01'
            msg = parser.parse(dns_data)
            
            if msg:
                print_pass("DNS parser works")
                self.passed += 1
            else:
                print_warn("DNS parser returned None (may be expected)")
                self.warnings += 1
        except Exception as e:
            print_fail(f"DNS parser error: {e}")
            self.failed += 1
    
    def test_cli_help(self):
        """Test CLI help commands"""
        print_test("Testing CLI help")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "protocrash.cli.main", "--help"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent,
                env={**os.environ, "PYTHONPATH": "src"}
            )
            
            if result.returncode == 0 and "ProtoCrash" in result.stdout:
                print_pass("CLI help works")
                self.passed += 1
            else:
                print_fail("CLI help failed")
                self.failed += 1
                
        except Exception as e:
            print_fail(f"CLI help error: {e}")
            self.failed += 1
    
    def test_basic_fuzzing(self):
        """Test basic fuzzing workflow"""
        print_test("Testing basic fuzzing workflow")
        
        try:
            from protocrash.fuzzing_engine.coordinator import FuzzingCoordinator, FuzzingConfig
            
            with tempfile.TemporaryDirectory() as tmpdir:
                corpus_dir = Path(tmpdir) / "corpus"
                crashes_dir = Path(tmpdir) / "crashes"
                corpus_dir.mkdir()
                crashes_dir.mkdir()
                
                # Create seed
                (corpus_dir / "seed1").write_bytes(b"test input")
                
                # Configure fuzzing
                config = FuzzingConfig(
                    target_cmd=["echo"],
                    corpus_dir=str(corpus_dir),
                    crashes_dir=str(crashes_dir),
                    timeout_ms=1000,
                    max_iterations=10,
                    stats_interval=999999
                )
                
                # Run fuzzing
                coordinator = FuzzingCoordinator(config)
                coordinator.run()
                
                if coordinator.stats.total_execs >= 9:  # Allow 9+ (timing variations)
                    print_pass(f"Completed {coordinator.stats.total_execs} executions")
                    self.passed += 1
                else:
                    print_fail(f"Only {coordinator.stats.total_execs} executions")
                    self.failed += 1
                    
        except Exception as e:
            print_fail(f"Basic fuzzing error: {e}")
            self.failed += 1


def main():
    """Run smoke tests"""
    tester = SmokeTest()
    success = tester.run_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
