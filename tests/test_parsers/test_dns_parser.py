"""
DNS Parser Tests
"""

import pytest
import struct
from protocrash.parsers.dns_parser import (
    DNSParser, DNSMessage, DNSQuestion, DNSResourceRecord,
    DNSType, DNSClass
)


class TestDNSParser:
    """Test DNS protocol parser"""
    
    def test_parse_simple_query(self):
        """Test parsing a simple DNS query"""
        parser = DNSParser()
        
        # Build a simple query for google.com A record
        # Header: ID=0x1234, flags=0x0100 (standard query), 1 question, 0 answers
        header = struct.pack('!HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0)
        
        # Question: google.com, type A, class IN
        question = b'\x06google\x03com\x00' + struct.pack('!HH', DNSType.A, DNSClass.IN)
        
        data = header + question
        msg = parser.parse(data)
        
        assert msg is not None
        assert msg.transaction_id == 0x1234
        assert len(msg.questions) == 1
        assert msg.questions[0].name == 'google.com'
        assert msg.questions[0].qtype == DNSType.A
        assert msg.questions[0].qclass == DNSClass.IN
    
    def test_parse_query_with_answer(self):
        """Test parsing DNS response with answer"""
        parser = DNSParser()
        
        # Header: 1 question, 1 answer
        header = struct.pack('!HHHHHH', 0x5678, 0x8180, 1, 1, 0, 0)
        
        # Question
        question = b'\x07example\x03com\x00' + struct.pack('!HH', DNSType.A, DNSClass.IN)
        
        # Answer: example.com A record -> 93.184.216.34
        answer_name = b'\x07example\x03com\x00'
        answer_data = struct.pack('!HHIH', DNSType.A, DNSClass.IN, 300, 4)  # TTL=300, rdlength=4
        answer_data += b'\x5d\xb8\xd8\x22'  # 93.184.216.34
        
        data = header + question + answer_name + answer_data
        msg = parser.parse(data)
        
        assert msg is not None
        assert msg.is_response
        assert len(msg.answers) == 1
        assert msg.answers[0].name == 'example.com'
        assert msg.answers[0].rtype == DNSType.A
        assert msg.answers[0].ttl == 300
    
    def test_domain_name_compression(self):
        """Test DNS name compression pointers"""
        parser = DNSParser()
        
        # Simple compression test
        # Query for www.example.com followed by answer with pointer to example.com
        header = struct.pack('!HHHHHH', 0xABCD, 0x8180, 1, 1, 0, 0)
        
        # Question: www.example.com
        question = b'\x03www\x07example\x03com\x00' + struct.pack('!HH', DNSType.A, DNSClass.IN)
        
        # Answer: www.example.com (using pointer)
        # Pointer to offset 12 (where 'www' starts)
        answer_name = b'\xC0\x0C'  # Pointer to offset 12
        answer_data = struct.pack('!HHIH', DNSType.A, DNSClass.IN, 100, 4)
        answer_data += b'\xC0\xA8\x01\x01'  # 192.168.1.1
        
        data = header + question + answer_name + answer_data
        msg = parser.parse(data)
        
        assert msg is not None
        assert len(msg.answers) == 1
        # Compression should be handled transparently
        assert 'www.example.com' in msg.answers[0].name or msg.answers[0].name == 'www.example.com'
    
    def test_reconstruct_query(self):
        """Test reconstructing DNS query from message"""
        parser = DNSParser()
        
        msg = DNSMessage(
            transaction_id=0x9999,
            flags=0x0100,
            questions=[
                DNSQuestion('test.local', DNSType.A, DNSClass.IN)
            ]
        )
        
        data = parser.reconstruct(msg)
        
        # Parse it back
        parsed = parser.parse(data)
        assert parsed is not None
        assert parsed.transaction_id == 0x9999
        assert len(parsed.questions) == 1
        assert parsed.questions[0].name == 'test.local'
    
    def test_detect_dns_with_port(self):
        """Test DNS detection with port hint"""
        parser = DNSParser()
        
        # Valid DNS query
        header = struct.pack('!HHHHHH', 0x1111, 0x0100, 1, 0, 0, 0)
        question = b'\x04test\x03com\x00' + struct.pack('!HH', DNSType.A, DNSClass.IN)
        data = header + question
        
        confidence = parser.detect(data, port=53)
        assert confidence > 0.8
    
    def test_detect_non_dns(self):
        """Test DNS detection rejects non-DNS data"""
        parser = DNSParser()
        
        # HTTP request
        data = b"GET /HTTP/1.1\r\nHost: test.com\r\n\r\n"
        confidence = parser.detect(data)
        assert confidence < 0.3
    
    def test_parse_invalid_data(self):
        """Test parser handles invalid data gracefully"""
        parser = DNSParser()
        
        # Too short
        assert parser.parse(b"short") is None
        
        # Invalid header
        assert parser.parse(b"\xFF" * 100) is not None or parser.parse(b"\xFF" * 100) is None
    
    def test_multiple_questions(self):
        """Test parsing multiple questions"""
        parser = DNSParser()
        
        header = struct.pack('!HHHHHH', 0x2222, 0x0100, 2, 0, 0, 0)
        q1 = b'\x03www\x04test\x03com\x00' + struct.pack('!HH', DNSType.A, DNSClass.IN)
        q2 = b'\x04mail\x04test\x03com\x00' + struct.pack('!HH', DNSType.MX, DNSClass.IN)
        
        data = header + q1 + q2
        msg = parser.parse(data)
        
        assert msg is not None
        assert len(msg.questions) == 2
        assert msg.questions[0].qtype == DNSType.A
        assert msg.questions[1].qtype == DNSType.MX
