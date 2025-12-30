"""
SMTP Parser Tests
"""

import pytest
from protocrash.parsers.smtp_parser import (
    SMTPParser, SMTPMessage, SMTPCommandLine, SMTPResponse
)


class TestSMTPParser:
    """Test SMTP protocol parser"""
    
    def test_parse_helo_command(self):
        """Test parsing HELO command"""
        parser = SMTPParser()
        
        data = b"HELO client.example.com\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        assert msg.is_client_message
        assert len(msg.commands) == 1
        assert msg.commands[0].verb == "HELO"
        assert "client.example.com" in msg.commands[0].argument
    
    def test_parse_mail_from(self):
        """Test parsing MAIL FROM command"""
        parser = SMTPParser()
        
        data = b"MAIL FROM:<sender@example.com>\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        assert len(msg.commands) == 1
        assert msg.commands[0].verb == "MAIL"
        assert "<sender@example.com>" in msg.commands[0].argument
    
    def test_parse_multiple_commands(self):
        """Test parsing command sequence"""
        parser = SMTPParser()
        
        data = b"HELO test.local\r\nMAIL FROM:<test@test.com>\r\nRCPT TO:<user@example.com>\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        assert len(msg.commands) == 3
        assert msg.commands[0].verb == "HELO"
        assert msg.commands[1].verb == "MAIL"
        assert msg.commands[2].verb == "RCPT"
    
    def test_parse_response_220(self):
        """Test parsing server greeting"""
        parser = SMTPParser()
        
        data = b"220 mail.example.com ESMTP Service ready\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        assert msg.is_server_message
        assert len(msg.responses) == 1
        assert msg.responses[0].code == 220
        assert"ESMTP" in msg.responses[0].message or "Service" in msg.responses[0].message
    
    def test_parse_multiline_response(self):
        """Test parsing multiline SMTP response"""
        parser = SMTPParser()
        
        data = b"250-mail.example.com\r\n250-SIZE 35651584\r\n250 HELP\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        assert len(msg.responses) == 1
        assert msg.responses[0].code == 250
        assert msg.responses[0].is_multiline
    
    def test_parse_data_command(self):
        """Test parsing DATA command with content"""
        parser = SMTPParser()
        
        data = b"DATA\r\nSubject: Test\r\nFrom: test@test.com\r\n\r\nHello World\r\n.\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        assert len(msg.commands) >= 1
        assert msg.commands[0].verb == "DATA"
        assert msg.data_content is not None
        assert b"Subject: Test" in msg.data_content
    
    def test_reconstruct_commands(self):
        """Test reconstructing SMTP commands"""
        parser = SMTPParser()
        
        msg = SMTPMessage()
        msg.commands = [
            SMTPCommandLine("HELO", "test.local"),
            SMTPCommandLine("QUIT", "")
        ]
        
        data = parser.reconstruct(msg)
        
        # Parse it back
        parsed = parser.parse(data)
        assert parsed is not None
        assert len(parsed.commands) == 2
        assert parsed.commands[0].verb == "HELO"
        assert parsed.commands[1].verb == "QUIT"
    
    def test_reconstruct_responses(self):
        """Test reconstructing SMTP responses"""
        parser = SMTPParser()
        
        msg = SMTPMessage()
        msg.responses = [
            SMTPResponse(220, "Service ready"),
            SMTPResponse(250, "OK")
        ]
        
        data = parser.reconstruct(msg)
        
        # Parse it back
        parsed = parser.parse(data)
        assert parsed is not None
        assert len(parsed.responses) == 2
        assert parsed.responses[0].code == 220
        assert parsed.responses[1].code == 250
    
    def test_detect_smtp_with_port(self):
        """Test SMTP detection with port hint"""
        parser = SMTPParser()
        
        data = b"220 smtp.example.com ESMTP Postfix\r\n"
        confidence = parser.detect(data, port=25)
        
        assert confidence > 0.8
    
    def test_detect_smtp_command(self):
        """Test SMTP detection for client commands"""
        parser = SMTPParser()
        
        data = b"EHLO client.example.com\r\n"
        confidence = parser.detect(data)
        
        assert confidence >= 0.6
    
    def test_detect_non_smtp(self):
        """Test SMTP detection rejects non-SMTP data"""
        parser = SMTPParser()
        
        # DNS data
        data = b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
        confidence = parser.detect(data)
        
        assert confidence < 0.3
    
    def test_parse_ehlo(self):
        """Test parsing EHLO (extended HELO)"""
        parser = SMTPParser()
        
        data = b"EHLO [192.168.1.1]\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        assert msg.commands[0].verb == "EHLO"
    
    def test_parse_error_response(self):
        """Test parsing error responses"""
        parser = SMTPParser()
        
        data = b"550 Requested action not taken: mailbox unavailable\r\n"
        msg = parser.parse(data)
        
        assert msg is not None
        assert msg.responses[0].code == 550
        assert "mailbox" in msg.responses[0].message.lower()
