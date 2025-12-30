"""
Tests for HttpParser - Enhanced
"""

import pytest
from protocrash.parsers.http_parser import HttpParser, HttpRequest

class TestHttpParser:
    """Test HTTP Parser"""

    def test_parse_simple_get(self):
        """Test parsing simple GET request"""
        raw = b"GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n"
        req = HttpParser.parse(raw)
        
        assert req is not None
        assert req.method == "GET"
        assert req.path == "/index.html"
        assert req.version == "HTTP/1.1"
        assert "Host" in req.headers
        assert req.headers["Host"] == ["example.com"]
        assert req.body == b""

    def test_parse_post_with_body(self):
        """Test parsing POST with body"""
        raw = b"POST /api/login HTTP/1.1\r\nContent-Length: 7\r\n\r\nuser=1"
        req = HttpParser.parse(raw)
        
        assert req is not None
        assert req.method == "POST"
        assert req.body == b"user=1"

    def test_duplicate_headers(self):
        """Test duplicate header support"""
        raw = b"GET / HTTP/1.1\r\nCookie: session=abc\r\nCookie: user=123\r\n\r\n"
        req = HttpParser.parse(raw)
        
        assert req is not None
        assert "Cookie" in req.headers
        assert len(req.headers["Cookie"]) == 2
        assert "session=abc" in req.headers["Cookie"]
        assert "user=123" in req.headers["Cookie"]

    def test_chunked_encoding_parse(self):
        """Test chunked encoding parsing"""
        raw = b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nHello\r\n0\r\n\r\n"
        req = HttpParser.parse(raw)
        
        assert req is not None
        assert req.is_chunked == True
        assert req.body == b"Hello"

    def test_chunked_encoding_reconstruct(self):
        """Test chunked encoding reconstruction"""
        req = HttpRequest(
            method="POST",
            path="/",
            headers={"Transfer-Encoding": ["chunked"]},
            body=b"Test",
            is_chunked=True
        )
        
        reconstructed = HttpParser.reconstruct(req)
        assert b"Transfer-Encoding: chunked" in reconstructed
        assert b"4\r\nTest\r\n0\r\n\r\n" in reconstructed

    def test_query_params(self):
        """Test query parameter extraction"""
        raw = b"GET /search?q=test&page=1 HTTP/1.1\r\n\r\n"
        req = HttpParser.parse(raw)
        
        assert req is not None
        assert "q" in req.query_params
        assert "page" in req.query_params
        assert req.query_params["q"] == ["test"]
        assert req.query_params["page"] == ["1"]

    def test_reconstruct(self):
        """Test reconstruction matches input (mostly)"""
        raw = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
        req = HttpParser.parse(raw)
        reconstructed = HttpParser.reconstruct(req)
        
        assert b"GET / HTTP/1.1" in reconstructed
        assert b"Host: localhost" in reconstructed
        assert reconstructed.endswith(b"\r\n\r\n")

    def test_invalid_input(self):
        """Test invalid input returns None"""
        assert HttpParser.parse(b"NOT_HTTP") is None
        assert HttpParser.parse(b"") is None
        # Test split failure handling
        assert HttpParser.parse(b"JUST_ONE_LINE") is None

    def test_malformed_headers(self):
        """Test headers without colon"""
        raw = b"GET / HTTP/1.1\r\nInvalidHeader\r\n\r\n"
        req = HttpParser.parse(raw)
        # Should parse request line but skip invalid header
        assert req is not None
        assert req.method == "GET"
        assert len(req.headers) == 0
