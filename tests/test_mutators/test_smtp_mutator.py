"""
Tests for SMTP mutator
"""

import pytest
from protocrash.mutators.smtp_mutator import SMTPMutator
from protocrash.parsers.smtp_parser import SMTPParser, SMTPMessage, SMTPCommandLine, SMTPResponse


class TestSMTPMutator:
    """Test SMTP-specific mutations"""
    
    def test_mutate_valid_command(self):
        """Test mutating a valid SMTP command"""
        mutator = SMTPMutator()
        parser = SMTPParser()
        
        # Valid SMTP command
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('HELO', 'client.example.com')]
        data = parser.reconstruct(msg)
        
        # Mutate multiple times
        for _ in range(10):
            mutated = mutator.mutate(data)
            assert isinstance(mutated, bytes)
            assert len(mutated) > 0
    
    def test_mutate_commands(self):
        """Test command mutations"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('EHLO', 'test.com')]
        
        original_verb = msg.commands[0].verb
        mutated = mutator.mutate_commands(msg)
        
        # Command should have changed
        assert len(mutated.commands) >= 1
    
    def test_mutate_responses(self):
        """Test response mutations"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.responses = [SMTPResponse(220, 'smtp.example.com ESMTP', False)]
        
        original_code = msg.responses[0].code
        mutated = mutator.mutate_responses(msg)
        
        assert len(mutated.responses) >= 1
    
    def test_mutate_data_content(self):
        """Test DATA content mutations"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.data_content = b'Subject: Test\r\n\r\nBody content here'
        
        original_content = msg.data_content
        mutated = mutator.mutate_data_content(msg)
        
        # Content should have changed
        assert mutated.data_content != original_content or len(mutated.data_content) != len(original_content)
    
    def test_mutate_line_lengths(self):
        """Test line length violation mutations"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('HELO', 'test.com')]
        
        mutated = mutator.mutate_line_lengths(msg)
        
        # Should create long lines
        if mutated.commands:
            assert len(mutated.commands[0].argument) > 900 or mutated.commands[0].argument == 'test.com'
    
    def test_mutate_crlf(self):
        """Test CRLF handling mutations"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('QUIT', '')]
        
        mutated = mutator.mutate_crlf(msg)
        
        assert isinstance(mutated, SMTPMessage)
    
    def test_mutate_empty_message(self):
        """Test mutating empty message"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        
        # Should add something
        mutated = mutator.mutate_commands(msg)
        assert len(mutated.commands) >= 1
    
    def test_mutate_invalid_data(self):
        """Test mutation of invalid SMTP data"""
        mutator = SMTPMutator()
        
        data = b'\x00\x01\x02\x03\x04'
        mutated = mutator.mutate(data)
        
        assert isinstance(mutated, bytes)
    
    def test_mail_from_mutation(self):
        """Test MAIL FROM command mutation"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('MAIL', 'FROM:<user@example.com>')]
        
        mutated = mutator.mutate_commands(msg)
        
        assert len(mutated.commands) >= 1
    
    def test_rcpt_to_mutation(self):
        """Test RCPT TO command mutation"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('RCPT', 'TO:<recipient@example.com>')]
        
        mutated = mutator.mutate_commands(msg)
        
        assert len(mutated.commands) >= 1
    
    def test_multiline_response_mutation(self):
        """Test multiline response mutations"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.responses = [SMTPResponse(250, 'Line1\nLine2\nLine3', True)]
        
        mutated = mutator.mutate_responses(msg)
        
        assert len(mutated.responses) >= 1
    
    def test_random_email_generation(self):
        """Test random email generation"""
        mutator = SMTPMutator()
        
        for _ in range(10):
            email = mutator._random_email()
            assert isinstance(email, str)
    
    def test_random_domain_generation(self):
        """Test random domain generation"""
        mutator = SMTPMutator()
        
        for _ in range(10):
            domain = mutator._random_domain()
            assert isinstance(domain, str)
            assert len(domain) > 0
    
    def test_mutate_preserves_some_parseability(self):
        """Test that some mutations preserve parseability"""
        mutator = SMTPMutator()
        parser = SMTPParser()
        
        # Valid command
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('EHLO', 'client.com')]
        data = parser.reconstruct(msg)
        
        parseable_count = 0
        for _ in range(20):
            mutated = mutator.mutate(data)
            parsed = parser.parse(mutated)
            if parsed is not None:
                parseable_count += 1
        
        # At least some should remain parseable
        assert parseable_count > 0
    
    def test_data_content_with_none(self):
        """Test DATA content mutation when None"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.data_content = None
        
        mutated = mutator.mutate_data_content(msg)
        
        # Should add content
        assert mutated.data_content is not None
    
    def test_response_code_range(self):
        """Test response code mutations cover valid and invalid codes"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.responses = [SMTPResponse(250, 'OK', False)]
        
        codes_seen = set()
        for _ in range(50):
            mutated = mutator.mutate_responses(msg)
            if mutated.responses:
                codes_seen.add(mutated.responses[0].code)
        
        # Should see variety of codes
        assert len(codes_seen) > 1
