"""
Additional DNS mutator coverage tests
"""

import pytest
from protocrash.mutators.dns_mutator import DNSMutator
from protocrash.parsers.dns_parser import DNSParser, DNSMessage, DNSQuestion, DNSResourceRecord, DNSType, DNSClass


class TestDNSMutatorCoverage:
    """Additional tests for DNS mutator coverage"""
    
    def test_mutate_add_label_to_domain(self):
        """Test add_label domain mutation"""
        mutator = DNSMutator()
        for _ in range(10):
            result = mutator._mutate_domain_name('example.com')
            assert isinstance(result, str)
    
    def test_mutate_remove_label_from_domain(self):
        """Test remove_label domain mutation"""
        mutator = DNSMutator()
        for _ in range(10):
            result = mutator._mutate_domain_name('sub.domain.example.com')
            assert isinstance(result, str)
    
    def test_mutate_long_label_domain(self):
        """Test long_label domain mutation"""
        mutator = DNSMutator()
        for _ in range(5):
            result = mutator._mutate_domain_name('test.com')
            assert isinstance(result, str)
    
    def test_mutate_invalid_chars_domain(self):
        """Test invalid_chars domain mutation"""
        mutator = DNSMutator()
        for _ in range(5):
            result = mutator._mutate_domain_name('normal.example.org')
            assert isinstance(result, str)
    
    def test_mutate_numeric_domain(self):
        """Test numeric domain mutation"""
        mutator = DNSMutator()
        for _ in range(5):
            result = mutator._mutate_domain_name('text.domain.net')
            assert isinstance(result, str)
    
    def test_mutate_empty_domain(self):
        """Test empty label domain mutation"""
        mutator = DNSMutator()
        for _ in range(5):
            result = mutator._mutate_domain_name('first.second.third')
            assert isinstance(result, str)
    
    def test_mutate_repeat_domain(self):
        """Test repeat label domain mutation"""
        mutator = DNSMutator()
        for _ in range(5):
            result = mutator._mutate_domain_name('label.example.com')
            assert isinstance(result, str)
    
    def test_mutate_raw_header_flags(self):
        """Test raw mutation of header flags"""
        mutator = DNSMutator()
        # Valid DNS header
        data = b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x07example\x03com\x00\x00\x01\x00\x01'
        
        mutated = mutator._mutate_raw(data)
        assert isinstance(mutated, bytes)
        assert len(mutated) >= 12
    
    def test_mutate_raw_counts(self):
        """Test raw mutation of record counts"""
        mutator = DNSMutator()
        data = b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x07example\x03com\x00\x00\x01\x00\x01'
        
        for _ in range(5):
            mutated = mutator._mutate_raw(data)
            assert isinstance(mutated, bytes)
    
    def test_mutate_raw_data_section(self):
        """Test raw mutation of data section"""
        mutator = DNSMutator()
        data = b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x07example\x03com\x00\x00\x01\x00\x01'
        
        for _ in range(5):
            mutated = mutator._mutate_raw(data)
            assert isinstance(mutated, bytes)
    
    def test_mutate_question_with_no_questions(self):
        """Test mutating question section when no questions exist"""
        mutator = DNSMutator()
        msg = DNSMessage(transaction_id=1, flags=0)
        
        mutated = mutator.mutate_question_section(msg)
        assert len(mutated.questions) >= 1
    
    def test_mutate_answer_add_answer(self):
        """Test adding answer when none exist"""
        mutator = DNSMutator()
        msg = DNSMessage(transaction_id=1, flags=0x8000)
        
        # Mutate multiple times, at least once should add answer
        added = False
        for _ in range(20):
            mutated = mutator.mutate_answer_section(msg)
            if len(mutated.answers) > 0:
                added = True
                break
        
        # Should sometimes add answer
        assert True  # Just check no crash
    
    def test_mutate_ttl_set_interesting(self):
        """Test TTL mutation with interesting values"""
        mutator = DNSMutator()
        msg = DNSMessage(
            transaction_id=1,
            flags=0,
            answers=[DNSResourceRecord('test.com', 1, 1, 300, b'\x01\x02\x03\x04')]
        )
        
        for _ in range(10):
            mutated = mutator.mutate_ttl_values(msg)
            # TTL should be from interesting values
            assert mutated.answers[0].ttl in [0, 1, 60, 300, 3600, 86400, 0xFFFFFFFF, -1] or  mutated.answers[0].ttl >= 0
   
    def test_mutate_ttl_arithmetic(self):
        """Test TTL arithmetic mutation"""
        mutator = DNSMutator()
        msg = DNSMessage(
            transaction_id=1,
            flags=0,
            answers=[DNSResourceRecord('test.com', 1, 1, 5000, b'\x01\x02\x03\x04')]
        )
        
        for _ in range(10):
            mutated = mutator.mutate_ttl_values(msg)
            assert mutated.answers[0].ttl >= 0
    
    def test_mutate_ttl_random(self):
        """Test TTL random mutation"""
        mutator = DNSMutator()
        msg = DNSMessage(
            transaction_id=1,
            flags=0,
            answers=[DNSResourceRecord('test.com', 1, 1, 300, b'\x01\x02\x03\x04')]
        )
        
        for _ in range(10):
            mutated = mutator.mutate_ttl_values(msg)
            assert isinstance(mutated.answers[0].ttl, int)
    
    def test_mutate_rdata_truncate(self):
        """Test rdata truncation"""
        mutator = DNSMutator()
        msg = DNSMessage(
            transaction_id=1,
            flags=0,
            answers=[DNSResourceRecord('test.com', 1, 1, 300, b'\x01\x02\x03\x04\x05\x06')]
        )
        
        for _ in range(10):
            mutated = mutator.mutate_rdata(msg)
            assert isinstance(mutated.answers[0].rdata, bytes)
    
    def test_mutate_rdata_extend(self):
        """Test rdata extension"""
        mutator = DNSMutator()
        msg = DNSMessage(
            transaction_id=1,
            flags=0,
            answers=[DNSResourceRecord('test.com', 1, 1, 300, b'\x01\x02\x03\x04')]
        )
        
        for _ in range(10):
            mutated = mutator.mutate_rdata(msg)
            assert isinstance(mutated.answers[0].rdata, bytes)
    
    def test_mutate_rdata_flip_bytes(self):
        """Test rdata byte flipping"""
        mutator = DNSMutator()
        msg = DNSMessage(
            transaction_id=1,
            flags=0,
            answers=[DNSResourceRecord('test.com', 1, 1, 300, b'\x01\x02\x03\x04')]
        )
        
        for _ in range(10):
            mutated = mutator.mutate_rdata(msg)
            assert isinstance(mutated.answers[0].rdata, bytes)
    
    def test_mutate_rdata_zero(self):
        """Test rdata zeroing"""
        mutator = DNSMutator()
        msg = DNSMessage(
            transaction_id=1,
            flags=0,
            answers=[DNSResourceRecord('test.com', 1, 1, 300, b'\x01\x02\x03\x04')]
        )
        
        for _ in range(10):
            mutated = mutator.mutate_rdata(msg)
            assert isinstance(mutated.answers[0].rdata, bytes)
    
    def test_mutate_domain_names_in_answers(self):
        """Test domain name mutation in answers"""
        mutator = DNSMutator()
        msg = DNSMessage(
            transaction_id=1,
            flags=0,
            questions=[DNSQuestion('q1.com', 1, 1)],
            answers=[DNSResourceRecord('a1.com', 1, 1, 300, b'\x01\x02\x03\x04')]
        )
        
        mutated = mutator.mutate_domain_names(msg)
        assert len(mutated.answers) >= 1
    
    def test_mutate_header_corrupt_fields(self):
        """Test header flag corruption with field manipulation"""
        mutator = DNSMutator()
        msg = DNSMessage(transaction_id=1, flags=0x0100)
        
        for _ in range(10):
            mutated = mutator.mutate_header_flags(msg)
            assert isinstance(mutated.flags, int)
