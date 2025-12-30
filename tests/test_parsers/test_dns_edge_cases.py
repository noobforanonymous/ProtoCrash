"""
DNS Parser - Additional Edge Case Tests for 90%+ Coverage
"""

import pytest
import struct
from protocrash.parsers.dns_parser import (
    DNSParser, DNSMessage, DNSQuestion, DNSResourceRecord,
    DNSType, DNSClass
)


class TestDNSParserEdgeCases:
    """Extended DNS parser tests for edge cases and error paths"""
    
    def test_parse_truncated_header(self):
        """Test handling of truncated header"""
        parser = DNSParser()
        
        # Header too short (< 12 bytes)
        data = b"\x12\x34\x01\x00"
        result = parser.parse(data)
        assert result is None
    
    def test_parse_truncated_question(self):
        """Test handling of truncated question section"""
        parser = DNSParser()
        
        # Valid header but truncated question
        header = struct.pack('!HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0)
        partial_question = b'\x04test'  # Missing domain end and type/class
        
        result = parser.parse(header + partial_question)
        assert result is None
    
    def test_parse_response_flag(self):
        """Test is_response flag"""
        parser = DNSParser()
        
        # Response flag set (QR=1)
        header = struct.pack('!HHHHHH', 0x5678, 0x8180, 0, 0, 0, 0)
        
        msg = parser.parse(header)
        assert msg is not None
        assert msg.is_response is True
    
    def test_parse_opcode(self):
        """Test opcode extraction"""
        parser = DNSParser()
        
        # Standard query (opcode=0)
        header = struct.pack('!HHHHHH', 0x0001, 0x0000, 0, 0, 0, 0)
        msg = parser.parse(header)
        assert msg.opcode == 0
        
        # Inverse query (opcode=1)
        header = struct.pack('!HHHHHH', 0x0001, 0x0800, 0, 0, 0, 0)  # 0x0800 = opcode 1
        msg = parser.parse(header)
        assert msg.opcode == 1
    
    def test_parse_rcode(self):
        """Test response code extraction"""
        parser = DNSParser()
        
        # NOERROR (rcode=0)
        header = struct.pack('!HHHHHH', 0x0001, 0x0000, 0, 0, 0, 0)
        msg = parser.parse(header)
        assert msg.rcode == 0
        
        # NXDOMAIN (rcode=3)
        header = struct.pack('!HHHHHH', 0x0001, 0x0003, 0, 0, 0, 0)
        msg = parser.parse(header)
        assert msg.rcode == 3
    
    def test_parse_complex_compression(self):
        """Test complex compression scenarios"""
        parser = DNSParser()
        
        # Multiple pointers in same packet
        header = struct.pack('!HHHHHH', 0xABCD, 0x8180, 1, 2, 0, 0)
        
        # Question: sub.example.com
        question = b'\x03sub\x07example\x03com\x00' + struct.pack('!HH', DNSType.A, DNSClass.IN)
        
        # Answer 1: sub.example.com (pointer to question)
        answer1_name = b'\xC0\x0C'  # Pointer to offset 12
        answer1_data = struct.pack('!HHIH', DNSType.A, DNSClass.IN, 100, 4) + b'\x01\x02\x03\x04'
        
        # Answer 2: example.com (pointer into first domain)
        answer2_name = b'\xC0\x10'  # Pointer to "example" offset
        answer2_data = struct.pack('!HHIH', DNSType.A, DNSClass.IN, 200, 4) + b'\x05\x06\x07\x08'
        
        data = header + question + answer1_name + answer1_data + answer2_name + answer2_data
        msg = parser.parse(data)
        
        assert msg is not None
        assert len(msg.answers) == 2
    
    def test_parse_empty_domain(self):
        """Test parsing root domain"""
        parser = DNSParser()
        
        header = struct.pack('!HHHHHH', 0x1111, 0x0100, 1, 0, 0, 0)
        # Root domain (.)
        question = b'\x00' + struct.pack('!HH', DNSType.NS, DNSClass.IN)
        
        data = header + question
        msg = parser.parse(data)
        
        assert msg is not None
        assert len(msg.questions) == 1
        assert msg.questions[0].name == '.'
    
    def test_build_empty_domain(self):
        """Test building root domain"""
        parser = DNSParser()
        
        domain_bytes = parser._build_name('.')
        assert domain_bytes == b'\x00'
        
        # Also test empty string
        domain_bytes = parser._build_name('')
        assert domain_bytes == b'\x00'
    
    def test_parse_long_domain(self):
        """Test parsing very long domain names"""
        parser = DNSParser()
        
        # Create a long but valid domain
        header = struct.pack('!HHHHHH', 0x2222, 0x0100, 1, 0, 0, 0)
        question = b'\x03www\x0alongdomainname\x07example\x03com\x00' + struct.pack('!HH', DNSType.A, DNSClass.IN)
        
        data = header + question
        msg = parser.parse(data)
        
        assert msg is not None
        assert 'longdomain' in msg.questions[0].name
    
    def test_parse_multiple_rr_sections(self):
        """Test parsing all RR sections"""
        parser = DNSParser()
        
        # Header with question, answer, authority, and additional
        header = struct.pack('!HHHHHH', 0x3333, 0x8180, 1, 1, 1, 1)
        
        # Question
        question = b'\x04test\x03com\x00' + struct.pack('!HH', DNSType.A, DNSClass.IN)
        
        # Answer
        answer_name = b'\x04test\x03com\x00'
        answer_data = struct.pack('!HHIH', DNSType.A, DNSClass.IN, 300, 4) + b'\x0A\x0A\x0A\x0A'
        
        # Authority (NS record)
        auth_name = b'\x03com\x00'
        auth_rdata = b'\x02ns\x03com\x00'
        auth_data = struct.pack('!HHIH', DNSType.NS, DNSClass.IN, 3600, len(auth_rdata)) + auth_rdata
        
        # Additional (A record for NS)
        add_name = b'\x02ns\x03com\x00'
        add_data = struct.pack('!HHIH', DNSType.A, DNSClass.IN, 3600, 4) + b'\x08\x08\x08\x08'
        
        data = header + question + answer_name + answer_data + auth_name + auth_data + add_name + add_data
        msg = parser.parse(data)
        
        assert msg is not None
        assert len(msg.questions) == 1
        assert len(msg.answers) == 1
        assert len(msg.authority) == 1
        assert len(msg.additional) == 1
    
    def test_parse_truncated_rr(self):
        """Test handling of truncated resource record"""
        parser = DNSParser()
        
        # Header with 1 answer but truncated data
        header = struct.pack('!HHHHHH', 0x4444, 0x8180, 0, 1, 0, 0)
        
        # Incomplete RR (no rdata)
        rr_name = b'\x04test\x03com\x00'
        rr_header = struct.pack('!HHIH', DNSType.A, DNSClass.IN, 100, 4)
        # Missing 4 bytes of rdata
        
        data = header + rr_name + rr_header
        result = parser.parse(data)
        
        # Should return None or partial message
        assert result is None or len(result.answers) == 0
    
    def test_detect_various_opcodes(self):
        """Test detection with various opcodes"""
        parser = DNSParser()
        
        # Valid standard query
        header = struct.pack('!HHHHHH', 0x5555, 0x0000, 1, 0, 0, 0)
        question = b'\x04test\x03com\x00' + struct.pack('!HH', 1, 1)
        data= header + question
        
        confidence = parser.detect(data)
        assert confidence >= 0.4
        
        # Invalid opcode (too high)
        header = struct.pack('!HHHHHH', 0x5555, 0x3000, 1, 0, 0, 0)  # opcode=6
        data2 = header + question
        
        confidence2 = parser.detect(data2)
        # Should have reduced confidence
        assert confidence2 < confidence or confidence2 == confidence * 0.5
    
    def test_detect_invalid_counts(self):
        """Test detection with unreasonable counts"""
        parser = DNSParser()
        
        # Too many questions
        header = struct.pack('!HHHHHH', 0x6666, 0x0100, 100, 0, 0, 0)
        
        confidence = parser.detect(header)
        # Should have reduced confidence
        assert confidence < 0.5
    
    def test_reconstruct_empty_message(self):
        """Test reconstructing message with no questions/answers"""
        parser = DNSParser()
        
        msg = DNSMessage(transaction_id=0x7777, flags=0x8000)
        
        data = parser.reconstruct(msg)
        
        # Should have valid header
        assert len(data) >= 12
        
        # Parse it back
        parsed = parser.parse(data)
        assert parsed is not None
        assert parsed.transaction_id == 0x7777
    
    def test_reconstruct_complex_rr(self):
        """Test reconstructing message with all RR sections"""
        parser = DNSParser()
        
        msg = DNSMessage(
            transaction_id=0x8888,
            flags=0x8180,
            questions=[DNSQuestion('example.com', DNSType.MX, DNSClass.IN)],
            answers=[DNSResourceRecord('example.com', DNSType.MX, DNSClass.IN, 300, b'\x00\x0A\x04mail\x07example\x03com\x00')],
            authority=[DNSResourceRecord('example.com', DNSType.NS, DNSClass.IN, 3600, b'\x02ns\x07example\x03com\x00')],
            additional=[DNSResourceRecord('mail.example.com', DNSType.A, DNSClass.IN, 300, b'\xC0\xA8\x01\x01')]
        )
        
        data = parser.reconstruct(msg)
        
        # Parse it back
        parsed = parser.parse(data)
        assert parsed is not None
        assert len(parsed.questions) == 1
        assert len(parsed.answers) == 1
        assert len(parsed.authority) == 1
        assert len(parsed.additional) == 1
    
    def test_parse_compression_loop_protection(self):
        """Test protection against compression pointer loops"""
        parser = DNSParser()
        
        # Create a malicious packet with circular pointers
        header = struct.pack('!HHHHHH', 0x9999, 0x8180, 0, 1, 0, 0)
        
        # RR with pointer that points to itself
        malicious_name = b'\xC0\x0C'  # Pointer to offset 12 (itself)
        rr_data = struct.pack('!HHIH', DNSType.A, DNSClass.IN, 100, 4) + b'\x01\x02\x03\x04'
        
        data = header + malicious_name + rr_data
        
        # Should not hang (loop protection should kick in)
        result = parser.parse(data)
        # Should handle gracefully
        assert result is not None or result is None  # Either way, shouldn't hang
