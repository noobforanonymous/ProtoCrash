"""
HTTP Mutator - Final Coverage Tests
"""

import pytest
from protocrash.mutators.http_mutator import HttpMutator
from protocrash.parsers.http_parser import HttpRequest


class TestHttpMutatorFinalCoverage:
    """Tests to achieve 100% HTTP mutator coverage"""
    
    def test_body_truncate_exactly_10_bytes(self):
        """Test body truncation with exactly 10 bytes (line 119)"""
        mutator = HttpMutator()
        
        # Body with exactly 10 bytes
        body_10 = b"1234567890"
        
        # Run truncate multiple times
        results = []
        for _ in range(50):
            result = mutator._mutate_body(body_10)
            results.append(result)
        
        # With 10 bytes, truncate should sometimes return original
        assert body_10 in results
    
    def test_body_truncate_less_than_10_bytes(self):
        """Test that bodies < 10 always return as-is on truncate"""
        mutator = HttpMutator()
        
        small_bodies = [b"a", b"ab", b"abc", b"12345"]
        
        for body in small_bodies:
            # Force many mutations to hit truncate path
            results = []
            for _ in range(40):
                result = mutator._mutate_body(body)
                results.append(result)
            
            # Small body should appear in results (from truncate returning it)
            assert body in results
    
    def test_chunked_with_existing_transfer_encoding(self):
        """Test chunked mutation when Transfer-Encoding already exists (branch 172->176)"""
        mutator = HttpMutator()
        
        # Request with existing Transfer-Encoding
        req = HttpRequest(
            "POST", 
            "/", 
            headers={"Transfer-Encoding": ["gzip"]}, 
            body=b"test"
        )
        
        mutator._mutate_chunked_encoding(req)
        
        # Should have modified Transfer-Encoding
        assert "Transfer-Encoding" in req.headers
        assert len(req.headers["Transfer-Encoding"]) > 0
        assert req.is_chunked == True
    
    def test_chunked_mutation_branch_coverage(self):
        """Ensure chunked strategy executes and returns properly"""
        mutator = HttpMutator()
        
        # Force chunked mutation many times
        raw = b"POST / HTTP/1.1\r\nHost: test\r\n\r\nbody"
        
        mutated_results = []
        for _ in range(100):
            result = mutator.mutate(raw)
            assert isinstance(result, bytes)
            mutated_results.append(result)
        
        # Verify we got different mutations
        assert len(set(mutated_results)) > 5
