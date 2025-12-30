"""
Additional SMTP mutator coverage tests
"""

import pytest
from protocrash.mutators.smtp_mutator import SMTPMutator
from protocrash.parsers.smtp_parser import SMTPParser, SMTPMessage, SMTPCommandLine, SMTPResponse


class TestSMTPMutatorCoverage:
    """Additional tests for SMTP mutator coverage"""
    
    def test_mutate_argument_mail_from(self):
        """Test MAIL FROM argument mutation"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('MAIL', 'FROM:<user@example.com>')]
        
        for _ in range(10):
            mutated = mutator.mutate_commands(msg)
            assert len(mutated.commands) >= 1
    
    def test_mutate_argument_rcpt_to(self):
        """Test RCPT TO argument mutation"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('RCPT', 'TO:<user@example.com>')]
        
        for _ in range(10):
            mutated = mutator.mutate_commands(msg)
            assert len(mutated.commands) >= 1
    
    def test_mutate_argument_helo(self):
        """Test HELO domain argument mutation"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('HELO', 'client.example.com')]
        
        for _ in range(10):
            mutated = mutator.mutate_commands(msg)
            assert len(mutated.commands) >= 1
    
    def test_mutate_argument_ehlo(self):
        """Test EHLO domain argument mutation"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('EHLO', 'client.example.com')]
        
        for _ in range(10):
            mutated = mutator.mutate_commands(msg)
            assert len(mutated.commands) >= 1
    
    def test_mutate_argument_vrfy(self):
        """Test VRFY username argument mutation"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('VRFY', 'username')]
        
        for _ in range(10):
            mutated = mutator.mutate_commands(msg)
            assert len(mutated.commands) >= 1
    
    def test_mutate_argument_generic(self):
        """Test generic argument mutation"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('HELP', 'MAIL')]
        
        for _ in range(10):
            mutated = mutator.mutate_commands(msg)
            assert len(mutated.commands) >= 1
    
    def test_mutate_data_content_headers(self):
        """Test DATA content header mutation"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.data_content = b'From: sender@example.com\r\nTo: recipient@example.com\r\n\r\nBody'
        
        for _ in range(10):
            mutated = mutator.mutate_data_content(msg)
            assert mutated.data_content is not None
    
    def test_mutate_data_content_body(self):
        """Test DATA content body mutation"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.data_content = b'Subject: Test\r\n\r\nThis is the body'
        
        for _ in range(10):
            mutated = mutator.mutate_data_content(msg)
            assert isinstance(mutated.data_content, bytes)
    
    def test_mutate_data_content_boundaries(self):
        """Test DATA content boundary mutation"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.data_content = b'Subject: Test\r\n\r\nLine1\r\nLine2'
        
        for _ in range(10):
            mutated = mutator.mutate_data_content(msg)
            assert isinstance(mutated.data_content, bytes)
    
    def test_mutate_data_content_size_large(self):
        """Test DATA content size mutation (large)"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.data_content = b'Small content'
        
        for _ in range(10):
            mutated = mutator.mutate_data_content(msg)
            assert isinstance(mutated.data_content, bytes)
    
    def test_mutate_data_content_size_small(self):
        """Test DATA content size mutation (small)"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.data_content = b'Large content' * 1000
        
        for _ in range(10):
            mutated = mutator.mutate_data_content(msg)
            assert isinstance(mutated.data_content, bytes)
    
    def test_mutate_raw_flip(self):
        """Test raw byte flipping"""
        mutator = SMTPMutator()
        data = b'HELO client.example.com\r\n'
        
        for _ in range(5):
            mutated = mutator._mutate_raw(data)
            assert isinstance(mutated, bytes)
    
    def test_mutate_raw_insert(self):
        """Test raw byte insertion"""
        mutator = SMTPMutator()
        data = b'MAIL FROM:<user@example.com>\r\n'
        
        for _ in range(5):
            mutated = mutator._mutate_raw(data)
            assert isinstance(mutated, bytes)
    
    def test_mutate_raw_delete(self):
        """Test raw byte deletion"""
        mutator = SMTPMutator()
        data = b'RCPT TO:<recipient@example.com>\r\n' * 5
        
        for _ in range(5):
            mutated = mutator._mutate_raw(data)
            assert isinstance(mutated, bytes)
    
    def test_mutate_raw_replace(self):
        """Test raw byte replacement"""
        mutator = SMTPMutator()
        data = b'QUIT\r\n' * 10
        
        for _ in range(5):
            mutated = mutator._mutate_raw(data)
            assert isinstance(mutated, bytes)
    
    def test_random_email_variations(self):
        """Test random email generation variations"""
        mutator = SMTPMutator()
        
        emails = set()
        for _ in range(50):
            email = mutator._random_email()
            emails.add(email)
        
        # Should generate variety
        assert len(emails) > 1
    
    def test_random_domain_variations(self):
        """Test random domain generation variations"""
        mutator = SMTPMutator()
        
        domains = []
        for _ in range(20):
            domain = mutator._random_domain()
            domains.append(domain)
            assert isinstance(domain, str)
            assert len(domain) > 0
    
    def test_random_string_various_lengths(self):
        """Test random string generation"""
        mutator = SMTPMutator()
        
        for length in [10, 50, 100, 500]:
            s = mutator._random_string(length)
            assert isinstance(s, str)
            assert len(s) == length
    
    def test_random_date_generation(self):
        """Test random date generation"""
        mutator = SMTPMutator()
        
        dates = []
        for _ in range(10):
            date = mutator._random_date()
            dates.append(date)
            assert isinstance(date, str)
            assert 'Jan' in date or '2' in date
    
    def test_response_message_mutations(self):
        """Test response message mutation variations"""
        mutator = SMTPMutator()
        
        messages = set()
        for _ in range(20):
            msg = mutator._mutate_response_message('Original message')
            messages.add(msg)
        
        # Should generate variety
        assert len(messages) > 1
    
    def test_mutate_line_lengths_commands(self):
        """Test line length mutation on commands"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('HELO', 'short'), SMTPCommandLine('MAIL', 'FROM:<test@test.com>')]
        
        mutated = mutator.mutate_line_lengths(msg)
        
        # At least one should be very long
        assert any(len(cmd.argument) > 900 for cmd in mutated.commands)
    
    def test_mutate_line_lengths_responses(self):
        """Test line length mutation on responses"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        msg.responses = [SMTPResponse(220, 'Short message', False)]
        
        mutated = mutator.mutate_line_lengths(msg)
        
        # Message should be very long
        assert len(mutated.responses[0].message) > 900
    
    def test_mutate_crlf_with_empty_message(self):
        """Test CRLF mutation with empty message"""
        mutator = SMTPMutator()
        msg = SMTPMessage()
        
        mutated = mutator.mutate_crlf(msg)
        
        # Should add default command
        assert len(mutated.commands) >= 1
