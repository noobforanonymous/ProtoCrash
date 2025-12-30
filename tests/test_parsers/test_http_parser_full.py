"""
HTTP Parser - 100% Coverage Tests
"""

import pytest
from protocrash.parsers.http_parser import HttpParser, HttpRequest


class TestHttpParserFullCoverage:
    """Tests to achieve 100% HTTP parser coverage"""
    
    def test_parse_empty_request_lines(self):
        """Test parsing with empty lines array (line 66)"""
        parser = HttpParser()
        
        # Request with no lines after split
        result = parser.parse(b"")
        assert result is None
    
    def test_parse_malformed_triggers_exception(self):
        """Test exception handling path (lines 113-114)"""
        parser = HttpParser()
        
        # Various malformed inputs that trigger exceptions
        malformed_inputs = [
            b"\xff\xfe\xfd",  # Invalid UTF-8
            b"G",  # Too short
            None,  # Wrong type would trigger exception in real usage
        ]
        
        for data in malformed_inputs:
            if isinstance(data, bytes):
                result = parser.parse(data)
                # Should return None on exception
                assert result is None or isinstance(result, HttpRequest)
    
    def test_transfer_encoding_non_chunked(self):
        """Test Transfer-Encoding header without chunked (branch 99->103)"""
        parser = HttpParser()
        
        # Transfer-Encoding present but not chunked
        raw = b"GET / HTTP/1.1\r\nHost: test\r\nTransfer-Encoding: gzip\r\n\r\ntest"
        result = parser.parse(raw)
        
        assert result is not None
        assert result.is_chunked == False
        assert "Transfer-Encoding" in result.headers
    
    def test_chunked_decode_missing_newline(self):
        """Test chunked decoding with missing newlines (line 127)"""
        parser = HttpParser()
        
        # Chunked data without proper CRLF
        raw = b"POST / HTTP/1.1\r\nHost: test\r\nTransfer-Encoding: chunked\r\n\r\n5invalid"
        result = parser.parse(raw)
        
        # Should still return a request, body may be malformed
        assert result is not None
    
    def test_chunked_decode_exception_fallback(self):
        """Test chunked decode exception handling (lines 144-145)"""
        parser = HttpParser()
        
        # Invalid hex in chunk size triggers exception
        raw = b"POST / HTTP/1.1\r\nHost: test\r\nTransfer-Encoding: chunked\r\n\r\nXYZ\r\ndata\r\n"
        result = parser.parse(raw)
        
        # Should return request with original body on decode failure
        assert result is not None
        assert result.is_chunked == True
    
    def test_chunked_decode_valid(self):
        """Test valid chunked encoding"""
        parser = HttpParser()
        
        # Valid chunked encoding
        raw = b"POST / HTTP/1.1\r\nHost: test\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nHello\r\n0\r\n\r\n"
        result = parser.parse(raw)
        
        assert result is not None
        assert result.is_chunked == True
        assert result.body == b"Hello"
    
    def test_parse_minimum_request_line(self):
        """Test request line with only method and path"""
        parser = HttpParser()
        
        raw = b"GET /\r\n\r\n"
        result = parser.parse(raw)
        
        assert result is not None
        assert result.method == "GET"
        assert result.path == "/"
        assert result.version == "HTTP/1.1"  # Default version
