"""
Tests for HttpMutator - Advanced
"""

import pytest
from unittest.mock import patch
from protocrash.mutators.http_mutator import HttpMutator
from protocrash.parsers.http_parser import HttpRequest

class TestHttpMutator:
    """Test HTTP Mutator"""

    def test_mutate_valid_http(self):
        """Test mutating valid HTTP request"""
        mutator = HttpMutator()
        raw = b"GET / HTTP/1.1\r\nHost: test\r\n\r\n"
        
        # Mutate multiple times to hit different strategies
        for _ in range(30):
            mutated = mutator.mutate(raw)
            assert mutated != raw
            assert len(mutated) > 0

    def test_mutate_invalid_http(self):
        """Test fallback mutation for invalid HTTP"""
        mutator = HttpMutator()
        raw = b"NOT_HTTP_DATA"
        
        mutated = mutator.mutate(raw)
        assert mutated != raw
        assert isinstance(mutated, bytes)

    def test_path_fuzzing(self):
        """Test path mutation uses payload library"""
        mutator = HttpMutator()
        req = HttpRequest("GET", "/", headers={})
        
        original_path = req.path
        mutated_path = mutator._mutate_path(original_path)
        
        # Should be from payloads library
        assert mutated_path in mutator.payloads.PATH_PAYLOADS

    def test_header_fuzzing(self):
        """Test header value mutation"""
        mutator = HttpMutator()
        req = HttpRequest("GET", "/", headers={"Host": ["example.com"]})
        
        mutator._mutate_header_value(req)
        # Should be modified
        assert req.headers["Host"][0] != "example.com"

    def test_cookie_fuzzing(self):
        """Test cookie mutation"""
        mutator = HttpMutator()
        req = HttpRequest("GET", "/", headers={})
        
        mutator._mutate_cookie(req)
        
        assert "Cookie" in req.headers
        assert len(req.headers["Cookie"]) > 0

    def test_smuggling_generation(self):
        """Test HTTP request smuggling payload generation"""
        mutator = HttpMutator()
        
        smuggled = mutator._create_smuggling_request()
        
        assert isinstance(smuggled, bytes)
        assert b"POST" in smuggled
        # Should have either Content-Length or Transfer-Encoding
        assert b"Content-Length" in smuggled or b"Transfer-Encoding" in smuggled

    def test_crlf_injection(self):
        """Test CRLF injection mutation"""
        mutator = HttpMutator()
        req = HttpRequest("GET", "/", headers={"Host": ["example.com"]})
        
        mutator._inject_crlf(req)
        
        # Should contain CRLF characters
        header_val = req.headers["Host"][0]
        assert "\r\n" in header_val

    def test_chunked_mutation(self):
        """Test chunked encoding mutation"""
        mutator = HttpMutator()
        req = HttpRequest("POST", "/", headers={}, body=b"test")
        
        mutator._mutate_chunked_encoding(req)
        
        assert req.is_chunked == True
        assert "Transfer-Encoding" in req.headers

    def test_method_mutation_advanced(self):
        """Test method mutation includes WebDAV"""
        mutator = HttpMutator()
        
        methods_found = set()
        for _ in range(50):
            method = mutator._mutate_method("GET")
            methods_found.add(method)
        
        # Should have varied methods
        assert len(methods_found) > 3
