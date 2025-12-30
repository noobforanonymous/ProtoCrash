"""
HTTP Mutator - Edge Case Coverage Tests
"""

import pytest
from protocrash.mutators.http_mutator import HttpMutator
from protocrash.parsers.http_parser import HttpRequest


class TestHttpMutatorEdgeCases:
    """Test edge cases for maximum HTTP mutator coverage"""
    
    def test_method_mutation_returns_current(self):
        """Test _mutate_method when random selects to return invalid method"""
        mutator = HttpMutator()
        
        # Run many times to hit the else branch (line 70-72)
        methods_seen = []
        for _ in range(100):
            method = mutator._mutate_method("GET")
            methods_seen.append(method)
            # Check for long random strings
            if len(method) > 10 and method.isupper():
                break
        
        # Should have hit the random string generation
        assert any(len(m) >= 10 for m in methods_seen)
    
    def test_fallback_mutate_empty_data(self):
        """Test _fallback_mutate with empty bytes (line 54)"""
        mutator = HttpMutator()
        
        result = mutator._fallback_mutate(b"")
        assert result == b""
    
    def test_mutate_header_value_empty_headers(self):
        """Test _mutate_header_value with no headers (line 81)"""
        mutator = HttpMutator()
        req = HttpRequest("GET", "/", headers={})
        
        # Should return early
        mutator._mutate_header_value(req)
        assert req.headers == {}
    
    def test_mutate_header_key_random_fuzz(self):
        """Test _mutate_header_key adding new header (lines 95-97)"""
        mutator = HttpMutator()
        req = HttpRequest("GET", "/", headers={})
        
        # Run many times to hit the if branch
        for _ in range(30):
            mutator._mutate_header_key(req)
        
        # Should have added at least one header
        assert len(req.headers) > 0
    
    def test_mutate_header_key_duplicate_existing(self):
        """Test _mutate_header_key duplicating header (line 100-102)"""
        mutator = HttpMutator()
        req = HttpRequest("GET", "/", headers={"Host": ["example.com"]})
        
        # Run many times to hit the else branch
        for _ in range(30):
            mutator._mutate_header_key(req)
        
        # Should have duplicated Host header
        assert len(req.headers["Host"]) > 1
    
    def test_mutate_body_all_techniques(self):
        """Test all body mutation techniques (lines 109-120)"""
        mutator = HttpMutator()
        
        # Test append
        results = set()
        for _ in range(100):
            result = mutator._mutate_body(b"test")
            results.add(len(result))
        
        # Should have hit append (longer), prepend (longer), replace (same), truncate (shorter)
        assert len(results) > 2  # Different lengths mean different techniques
    
    def test_mutate_body_empty_input(self):
        """Test _mutate_body with empty body (line 107)"""
        mutator = HttpMutator()
        
        result = mutator._mutate_body(b"")
        # Should return random A's
        assert len(result) >= 100
        assert all(b == ord('A') for b in result)
    
    def test_inject_crlf_empty_headers(self):
        """Test _inject_crlf with no headers (line 148)"""
        mutator = HttpMutator()
        req = HttpRequest("GET", "/", headers={})
        
        mutator._inject_crlf(req)
        
        # Should have added X-Fuzz header with CRLF payload
        assert "X-Fuzz" in req.headers
        assert len(req.headers["X-Fuzz"]) > 0
        # Check for injected header markers
        assert any("Injected" in v or "Set-Cookie" in v or "HTTP/1.1" in v for v in req.headers["X-Fuzz"])
    
    def test_mutate_chunked_no_transfer_encoding(self):
        """Test _mutate_chunked_encoding adding header (lines 168-172)"""
        mutator = HttpMutator()
        req = HttpRequest("POST", "/", headers={}, body=b"test")
        
        # Ensure no Transfer-Encoding initially
        assert "Transfer-Encoding" not in req.headers
        
        mutator._mutate_chunked_encoding(req)
        
        # Should have added Transfer-Encoding
        assert "Transfer-Encoding" in req.headers
        assert len(req.headers["Transfer-Encoding"]) > 0
    
    def test_mutate_with_method_strategy(self):
        """Force method mutation strategy (line 31)"""
        mutator = HttpMutator()
        
        # Create a request that will be parsed
        raw = b"GET / HTTP/1.1\r\nHost: test\r\n\r\n"
        
        # Mock random to always choose "method"
        import random
        original_choice = random.choice
        
        def mock_choice(seq):
            if isinstance(seq, list) and "method" in seq:
                return "method"
            return original_choice(seq)
        
        random.choice = mock_choice
        
        try:
            mutated = mutator.mutate(raw)
            assert mutated != raw
        finally:
            random.choice = original_choice
    
    def test_mutate_with_chunked_strategy(self):
        """Force chunked mutation strategy (lines 46-47)"""
        mutator = HttpMutator()
        raw = b"POST / HTTP/1.1\r\nHost: test\r\n\r\ntest body"
        
        # Run many times to eventually hit chunked
        for _ in range(50):
            mutated = mutator.mutate(raw)
            if b"Transfer-Encoding" in mutated or b"chunked" in mutated:
                break
        
        # Should have hit chunked at some point
        assert b"Transfer-Encoding" in mutated or b"chunked" in mutated
    
    def test_body_truncate_edge_case(self):
        """Test body truncation with small body (line 118-120)"""
        mutator = HttpMutator()
        
        # Test with body <= 10 bytes
        small_body = b"tiny"
        results = []
        for _ in range(30):
            result = mutator._mutate_body(small_body)
            results.append(result)
        
        # For small bodies, truncate should return original
        assert small_body in results
    
    def test_mutate_all_strategies_coverage(self):
        """Run enough mutations to hit all code paths"""
        mutator = HttpMutator()
        raw = b"POST /test HTTP/1.1\r\nHost: example.com\r\nCookie: session=abc\r\n\r\ntest body"
        
        # Run many mutations to ensure all strategies are hit
        for _ in range(200):
            mutated = mutator.mutate(raw)
            assert isinstance(mutated, bytes)
