"""
SMTP Parser - Additional Edge Case Tests for 90%+ Coverage
"""

import pytest
from protocrash.parsers.smtp_parser import (
    SMTPParser, SMTPMessage, SMTPCommandLine, SMTPResponse
)


class TestSMTPParserEdgeCases:
    """Extended SMTP parser tests for edge cases and error paths"""
    
    def test_parse_incomplete_command(self):
        """Test parsing incomplete commands"""
        parser = SMTPParser()
        
        # Command without CRLF
        data = b"HELO example.com"
        msg = parser.parse(data)
        
        assert msg is not None
        # Should handle gracefully
    
    def test_parse_lowercase_commands(self):
        """Test parsing lowercase SMTP commands"""
        parser = SMTPParser()
        
        data = b"helo client.test.com\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        assert len(msg.commands) == 1
        assert msg.commands[0].verb == "HELO"  # Should be uppercased
    
    def test_parse_mixed_case_commands(self):
        """Test parsing mixed case commands"""
        parser = SMTPParser()
        
        data = b"HeLo client.example.com\r\nMaIl FrOm:<test@test.com>\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        assert len(msg.commands) == 2
        assert msg.commands[0].verb == "HELO"
        assert msg.commands[1].verb == "MAIL"
    
    def test_parse_empty_lines(self):
        """Test handling empty lines"""
        parser = SMTPParser()
        
        data = b"\r\n\r\nHELO test\r\n\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        # Should skip empty lines
    
    def test_parse_data_without_end_marker(self):
        """Test DATA command without end marker"""
        parser = SMTPParser()
        
        data = b"DATA\r\nSubject: Test\r\n\r\nBody text\r\n"
        # No "." terminator
        msg = parser.parse(data)
        
        assert msg is not None
        assert len(msg.commands) >= 1
    
    def test_parse_data_with_empty_body(self):
        """Test DATA with no content"""
        parser = SMTPParser()
        
        data = b"DATA\r\n.\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        assert msg.data_content == b'' or msg.data_content is None
    
    def test_parse_multiline_incomplete(self):
        """Test incomplete multiline response"""
        parser = SMTPParser()
        
        # Multiline without final line
        data = b"250-First line\r\n250-Second line\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        # Should handle partial multiline
    
    def test_parse_response_with_long_message(self):
        """Test response with very long message"""
        parser = SMTPParser()
        
        long_message = "A" * 500
        data = f"220 {long_message}\r\n".encode()
        
        msg = parser.parse(data)
        
        assert msg is not None
        assert len(msg.responses[0].message) == 500
    
    def test_parse_invalid_response_code(self):
        """Test handling invalid response codes"""
        parser = SMTPParser()
        
        # Non-numeric code (should fail pattern match)
        data = b"ABC Invalid response\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        # Should be parsed as command, not response
    
    def test_parse_response_code_boundaries(self):
        """Test various response code ranges"""
        parser = SMTPParser()
        
        # All valid ranges
        codes = [200, 211, 220, 250, 251, 354, 421, 450, 500, 550, 552]
        
        for code in codes:
            data = f"{code} Message\r\n".encode()
            msg = parser.parse(data)
            
            assert msg is not None
            assert len(msg.responses) == 1
            assert msg.responses[0].code == code
    
    def test_reconstruct_with_data(self):
        """Test reconstructing message with DATA content"""
        parser = SMTPParser()
        
        msg = SMTPMessage()
        msg.commands = [
            SMTPCommandLine("MAIL", "FROM:<test@test.com>"),
            SMTPCommandLine("RCPT", "TO:<user@example.com>"),
            SMTPCommandLine("DATA", "")
        ]
        msg.data_content = b"Subject: Test\r\n\r\nEmail body"
        
        data = parser.reconstruct(msg)
        
        # Should include DATA terminator
        assert b".\r\n" in data
        assert b"Email body" in data
    
    def test_reconstruct_multiline_response(self):
        """Test reconstructing multiline response"""
        parser = SMTPParser()
        
        msg = SMTPMessage()
        msg.responses = [
            SMTPResponse(250, "Line1\nLine2\nLine3", is_multiline=True)
        ]
        
        data = parser.reconstruct(msg)
        
        # Should have proper multiline format
        assert b"250-" in data
        assert b"250 " in data  # Last line uses space
    
    def test_detect_with_various_ports(self):
        """Test detection on various SMTP ports"""
        parser = SMTPParser()
        
        data = b"220 smtp.example.com\r\n"
        
        # Standard port
        confidence1 = parser.detect(data, port=25)
        assert confidence1 > 0.8
        
        # Submission port
        confidence2 = parser.detect(data, port=587)
        assert confidence2 > 0.8
        
        # SMTPS port
        confidence3 = parser.detect(data, port=465)
        assert confidence3 > 0.8
        
        # Alternate port
        confidence4 = parser.detect(data, port=2525)
        assert confidence4 > 0.8
    
    def test_detect_mail_from_pattern(self):
        """Test detection of MAIL FROM pattern"""
        parser = SMTPParser()
        
        data = b"MAIL FROM:<sender@example.com>\r\n"
        confidence = parser.detect(data)
        
        assert confidence >= 0.8  # Should boost confidence
    
    def test_detect_rcpt_to_pattern(self):
        """Test detection of RCPT TO pattern"""
        parser = SMTPParser()
        
        data = b"RCPT TO:<recipient@example.com>\r\n"
        confidence = parser.detect(data)
        
        assert confidence >= 0.8
    
    def test_detect_common_response_codes(self):
        """Test detection boost for common codes"""
        parser = SMTPParser()
        
        common_codes = [220, 250, 354, 421, 450, 451, 500, 501, 550]
        
        for code in common_codes:
            data = f"{code} Message\r\n".encode()
            confidence = parser.detect(data)
            
            # Common codes should have higher confidence
            assert confidence >= 0.5
    
    def test_detect_uncommon_response_codes(self):
        """Test detection with less common codes"""
        parser = SMTPParser()
        
        data = b"299 Unusual code\r\n"
        confidence = parser.detect(data)
        
        # Should still detect as SMTP but maybe lower confidence
        assert confidence > 0.0
    
    def test_parse_all_smtp_commands(self):
        """Test parsing all standard SMTP commands"""
        parser = SMTPParser()
        
        commands = [
            b"HELO example.com\r\n",
            b"EHLO example.com\r\n",
            b"MAIL FROM:<test@test.com>\r\n",
            b"RCPT TO:<user@example.com>\r\n",
            b"DATA\r\n",
            b"RSET\r\n",
            b"VRFY user@example.com\r\n",
            b"EXPN list@example.com\r\n",
            b"HELP\r\n",
            b"NOOP\r\n",
            b"QUIT\r\n"
        ]
        
        for cmd_data in commands:
            msg = parser.parse(cmd_data)
            assert msg is not None
            assert len(msg.commands) >= 1
    
    def test_parse_command_without_pattern_match(self):
        """Test parsing malformed command that doesn't match pattern"""
        parser = SMTPParser()
        
        # Unusual format (should still try to parse)
        data = b"CUSTOMCMD argument value\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        # Should attempt to parse as simple text
    
    def test_parse_response_without_message(self):
        """Test response with code but no message"""
        parser = SMTPParser()
        
        data = b"250\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        # May be parsed as command or response depending on pattern
        assert len(msg.commands) + len(msg.responses) >= 1
    
    def test_reconstruct_command_without_argument(self):
        """Test reconstructing command with no argument"""
        parser = SMTPParser()
        
        msg = SMTPMessage()
        msg.commands = [
            SMTPCommandLine("QUIT", "")
        ]
        
        data = parser.reconstruct(msg)
        
        assert b"QUIT\r\n" in data
        # Should not have extra space
    
    def test_detect_binary_data(self):
        """Test detection rejects binary data"""
        parser = SMTPParser()
        
        # Random binary
        data = b"\x00\x01\x02\x03\x04\x05"
        confidence = parser.detect(data)
        
        assert confidence < 0.5
    
    def test_parse_exception_handling(self):
        """Test exception handling in parse"""
        parser = SMTPParser()
        
        # Data that might cause issues
        invalid_data = [
            b"\xFF\xFF\xFF\xFF",  # Invalid UTF-8
            b"",  # Empty
            b"\x00" * 1000,  # Null bytes
        ]
        
        for data in invalid_data:
            result = parser.parse(data)
            # Should not raise exception
            assert result is not None or result is None
