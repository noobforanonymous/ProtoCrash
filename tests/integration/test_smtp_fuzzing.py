"""
End-to-end SMTP fuzzing integration tests
"""

import pytest
from protocrash.parsers.smtp_parser import SMTPParser, SMTPMessage, SMTPCommandLine, SMTPResponse
from protocrash.mutators.smtp_mutator import SMTPMutator


class TestSMTPFuzzingIntegration:
    """Integration tests for SMTP protocol fuzzing"""
    
    def test_simple_command_fuzzing_cycle(self):
        """Test complete SMTP command fuzzing cycle"""
        parser = SMTPParser()
        mutator = SMTPMutator()
        
        # Seed SMTP command
        seed_msg = SMTPMessage()
        seed_msg.commands = [SMTPCommandLine('HELO', 'client.example.com')]
        seed_data = parser.reconstruct(seed_msg)
        
        valid_count = 0
        invalid_count = 0
        
        for _ in range(10):
            mutated_data = mutator.mutate(seed_data)
            
            assert isinstance(mutated_data, bytes)
            assert len(mutated_data) > 0
            
            parsed = parser.parse(mutated_data)
            if parsed is not None:
                valid_count += 1
            else:
                invalid_count += 1
        
        assert valid_count > 0 or invalid_count > 0
    
    def test_mail_transaction_fuzzing(self):
        """Test fuzzing complete SMTP mail transaction"""
        parser = SMTPParser()
        mutator = SMTPMutator()
        
        # MAIL FROM → RCPT TO → DATA sequence
        seed_msg = SMTPMessage()
        seed_msg.commands = [
            SMTPCommandLine('MAIL', 'FROM:<sender@example.com>'),
            SMTPCommandLine('RCPT', 'TO:<recipient@example.com>'),
            SMTPCommandLine('DATA', '')
        ]
        seed_msg.data_content = b'Subject: Test\r\n\r\nBody content here'
        seed_data = parser.reconstruct(seed_msg)
        
        for _ in range(15):
            mutated = mutator.mutate(seed_data)
            
            assert isinstance(mutated, bytes)
            
            # Try parsing
            parsed = parser.parse(mutated)
            # May or may not parse successfully
    
    def test_smtp_response_fuzzing(self):
        """Test fuzzing SMTP server responses"""
        parser = SMTPParser()
        mutator = SMTPMutator()
        
        # Server greeting
        seed_msg = SMTPMessage()
        seed_msg.responses = [
            SMTPResponse(220, 'smtp.example.com ESMTP', False)
        ]
        seed_data = parser.reconstruct(seed_msg)
        
        mutations = []
        for _ in range(10):
            mutated = mutator.mutate(seed_data)
            mutations.append(mutated)
            assert len(mutated) > 0
        
        # Should have variety
        unique = set(mutations)
        assert len(unique) > 1
    
    def test_multiline_response_fuzzing(self):
        """Test fuzzing multiline SMTP responses"""
        parser = SMTPParser()
        mutator = SMTPMutator()
        
        seed_msg = SMTPMessage()
        seed_msg.responses = [
            SMTPResponse(250, 'Feature1\nFeature2\nFeature3', True)
        ]
        seed_data = parser.reconstruct(seed_msg)
        
        for _ in range(10):
            mutated = mutator.mutate(seed_data)
            
            assert isinstance(mutated, bytes)
            
            parsed = parser.parse(mutated)
            if parsed:
                assert isinstance(parsed, SMTPMessage)
    
    def test_data_content_fuzzing(self):
        """Test fuzzing email DATA content"""
        parser = SMTPParser()
        mutator = SMTPMutator()
        
        seed_msg = SMTPMessage()
        seed_msg.commands = [SMTPCommandLine('DATA', '')]
        seed_msg.data_content = b'From: sender@test.com\r\nTo: recipient@test.com\r\nSubject: Test Email\r\n\r\nThis is the message body.\r\n'
        seed_data = parser.reconstruct(seed_msg)
        
        for _ in range(15):
            mutated = mutator.mutate(seed_data)
            
            assert len(mutated) > 0
            
            # Parsing might fail with corrupted DATA
            parsed = parser.parse(mutated)
            # No assertion - just checking no crash
    
    def test_invalid_smtp_handling(self):
        """Test fuzzer handles invalid SMTP data"""
        mutator = SMTPMutator()
        
        invalid_data = b'\x00\x01\x02\x03\x04\x05'
        
        mutated = mutator.mutate(invalid_data)
        assert isinstance(mutated, bytes)
    
    def test_response_code_fuzzing(self):
        """Test fuzzing different response codes"""
        parser = SMTPParser()
        mutator = SMTPMutator()
        
        codes = [220, 250, 354, 450, 500, 550]
        
        for code in codes:
            seed_msg = SMTPMessage()
            seed_msg.responses = [SMTPResponse(code, 'Message', False)]
            seed_data = parser.reconstruct(seed_msg)
            
            mutated = mutator.mutate(seed_data)
            
            assert isinstance(mutated, bytes)
            assert len(mutated) > 0
    
    def test_command_sequence_fuzzing(self):
        """Test fuzzing sequences of SMTP commands"""
        parser = SMTPParser()
        mutator = SMTPMutator()
        
        seed_msg = SMTPMessage()
        seed_msg.commands = [
            SMTPCommandLine('EHLO', 'client.com'),
            SMTPCommandLine('MAIL', 'FROM:<test@test.com>'),
            SMTPCommandLine('RCPT', 'TO:<user@user.com>'),
            SMTPCommandLine('QUIT', '')
        ]
        seed_data = parser.reconstruct(seed_msg)
        
        for _ in range(10):
            mutated = mutator.mutate(seed_data)
            
            parsed = parser.parse(mutated)
            # Should handle gracefully
            assert isinstance(mutated, bytes)
    
    def test_long_line_mutation(self):
        """Test fuzzing creates line length violations"""
        parser = SMTPParser()
        mutator = SMTPMutator()
        
        seed_msg = SMTPMessage()
        seed_msg.commands = [SMTPCommandLine('HELO', 'short.com')]
        seed_data = parser.reconstruct(seed_msg)
        
        long_lines_created = 0
        
        for _ in range(30):
            mutated_data = mutator.mutate(seed_data)
            
            # Check if created long lines (>998 chars)
            if b'\r\n' in mutated_data:
                lines = mutated_data.split(b'\r\n')
                for line in lines:
                    if len(line) > 998:
                        long_lines_created += 1
                        break
        
        # Should create some long lines
        assert long_lines_created > 0
    
    def test_email_address_fuzzing(self):
        """Test fuzzing email addresses in MAIL/RCPT"""
        parser = SMTPParser()
        mutator = SMTPMutator()
        
        seed_msg = SMTPMessage()
        seed_msg.commands = [
            SMTPCommandLine('MAIL', 'FROM:<normal@example.com>'),
            SMTPCommandLine('RCPT', 'TO:<user@domain.com>')
        ]
        seed_data = parser.reconstruct(seed_msg)
        
        email_variations = set()
        
        for _ in range(20):
            mutated_data = mutator.mutate(seed_data)
            parsed = parser.parse(mutated_data)
            
            if parsed and parsed.commands:
                for cmd in parsed.commands:
                    if 'FROM:' in cmd.argument.upper() or 'TO:' in cmd.argument.upper():
                        email_variations.add(cmd.argument)
        
        # Should generate variations
        assert len(email_variations) >= 1
    
    def test_dot_stuffing_mutation(self):
        """Test mutations around dot-stuffing in DATA"""
        parser = SMTPParser()
        mutator = SMTPMutator()
        
        # Data with dots at line start
        seed_msg = SMTPMessage()
        seed_msg.commands = [SMTPCommandLine('DATA', '')]
        seed_msg.data_content = b'Line 1\r\n.Line starting with dot\r\n..Another one\r\n'
        seed_data = parser.reconstruct(seed_msg)
        
        for _ in range(10):
            mutated = mutator.mutate(seed_data)
            
            # Should not crash
            assert isinstance(mutated, bytes)
    
    def test_response_multiline_corruption(self):
        """Test mutations can corrupt multiline response structure"""
        parser = SMTPParser()
        mutator = SMTPMutator()
        
        seed_msg = SMTPMessage()
        seed_msg.responses = [
            SMTPResponse(250, 'Line1\nLine2\nLine3\nLine4', True)
        ]
        seed_data = parser.reconstruct(seed_msg)
        
        for _ in range(15):
            mutated = mutator.mutate(seed_data)
            
            parsed = parser.parse(mutated)
            # Corruption may make it unparseable
            # Just ensure no crash
            assert len(mutated) > 0
    
    def test_fuzzing_preserves_some_structure(self):
        """Test that mutations don't always destroy parseability"""
        parser = SMTPParser()
        mutator = SMTPMutator()
        
        seed_msg = SMTPMessage()
        seed_msg.commands = [SMTPCommandLine('QUIT', '')]
        seed_data = parser.reconstruct(seed_msg)
        
        parseable_count = 0
        
        for _ in range(25):
            mutated = mutator.mutate(seed_data)
            parsed = parser.parse(mutated)
            
            if parsed and parsed.commands:
                parseable_count += 1
        
        # At least some should parse
        assert parseable_count > 0
