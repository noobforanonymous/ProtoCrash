"""
Protocol Registry and Detector Tests
"""

import pytest
from protocrash.core import ProtocolRegistry, ProtocolDetector
from protocrash.parsers.dns_parser import DNSParser
from protocrash.parsers.smtp_parser import SMTPParser


class TestProtocolRegistry:
    """Test protocol registry system"""
    
    def test_list_protocols(self):
        """Test listing registered protocols"""
        protocols = ProtocolRegistry.list_protocols()
        
        # DNS and SMTP should be auto-registered
        assert 'dns' in protocols or 'smtp' in protocols
    
    def test_get_parser(self):
        """Test retrieving parser by name"""
        parser_class = ProtocolRegistry.get_parser('dns')
        assert parser_class is not None
        
        parser = parser_class()
        assert parser.protocol_name == 'dns'
    
    def test_auto_detect_dns(self):
        """Test auto-detection of DNS"""
        import struct
        
        # DNS query
        header = struct.pack('!HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0)
        question = b'\x06google\x03com\x00' + struct.pack('!HH', 1, 1)
        data = header + question
        
        protocol, confidence = ProtocolRegistry.auto_detect(data, port=53)
        
        assert protocol == 'dns'
        assert confidence > 0.7
    
    def test_auto_detect_smtp(self):
        """Test auto-detection of SMTP"""
        data = b"220 smtp.example.com ESMTP\r\n"
        
        protocol, confidence = ProtocolRegistry.auto_detect(data, port=25)
        
        assert protocol == 'smtp'
        assert confidence > 0.7
    
    def test_auto_detect_unknown(self):
        """Test auto-detection with unknown protocol"""
        data = b"UNKNOWN PROTOCOL DATA HERE"
        
        protocol, confidence = ProtocolRegistry.auto_detect(data)
        
        # Should return None for low confidence
        assert protocol is None or confidence < 0.5


class TestProtocolDetector:
    """Test protocol detector"""
    
    def test_detect_with_port_hint(self):
        """Test detection with port hints"""
        detector = ProtocolDetector()
        
        # DNS on port 53
        import struct
        header = struct.pack('!HHHHHH', 0x5678, 0x0100, 1, 0, 0, 0)
        question = b'\x04test\x03com\x00' + struct.pack('!HH', 1, 1)
        data = header + question
        
        protocol, confidence = detector.detect(data, port=53)
        
        assert protocol == 'dns'
        assert confidence > 0.7
    
    def test_detect_with_fallback(self):
        """Test detection with fallback"""
        detector = ProtocolDetector()
        
        # Random binary data
        data = b"\xDE\xAD\xBE\xEF" * 10
        
        protocol, confidence = detector.detect_with_fallback(data)
        
        # Should fallback to binary
        assert protocol == 'binary'
        assert confidence == 0.1
    
    def test_port_hints_correct(self):
        """Test port hint mapping"""
        detector = ProtocolDetector()
        
        assert detector.PORT_HINTS[53] == 'dns'
        assert detector.PORT_HINTS[25] == 'smtp'
    
    def test_detect_smtp_on_alt_port(self):
        """Test SMTP detection on alternate ports"""
        detector = ProtocolDetector()
        
        data = b"220 mail.server.com ESMTP\r\n"
        
        # Port 587 (submission)
        protocol, confidence = detector.detect(data, port=587)
        assert protocol == 'smtp'
        
        # Port 465 (smtps)
        protocol, confidence = detector.detect(data, port=465)
        assert protocol == 'smtp'
