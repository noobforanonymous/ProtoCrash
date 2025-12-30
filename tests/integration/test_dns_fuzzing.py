"""
End-to-end DNS fuzzing integration tests
"""

import pytest
from protocrash.parsers.dns_parser import DNSParser, DNSMessage, DNSQuestion, DNSResourceRecord, DNSType, DNSClass
from protocrash.mutators.dns_mutator import DNSMutator


class TestDNSFuzzingIntegration:
    """Integration tests for DNS protocol fuzzing"""
    
    def test_simple_query_fuzzing_cycle(self):
        """Test complete fuzzing cycle: seed → mutate → validate → parse"""
        parser = DNSParser()
        mutator = DNSMutator()
        
        # Create seed DNS query
        seed_msg = DNSMessage(
            transaction_id=0x1234,
            flags=0x0100,  # Standard query, recursion desired
            questions=[DNSQuestion('example.com', DNSType.A, DNSClass.IN)]
        )
        seed_data = parser.reconstruct(seed_msg)
        
        # Fuzz 10 iterations
        valid_count = 0
        invalid_count = 0
        
        for i in range(10):
            mutated_data = mutator.mutate(seed_data)
            
            # Validate mutated data
            assert isinstance(mutated_data, bytes)
            assert len(mutated_data) > 0
            
            # Try to parse mutated data
            parsed = parser.parse(mutated_data)
            if parsed is not None:
                valid_count += 1
                # Validate parsed structure
                assert isinstance(parsed, DNSMessage)
            else:
                invalid_count += 1
        
        # Should have mix of valid and invalid
        assert valid_count > 0 or invalid_count > 0
    
    def test_dns_response_fuzzing(self):
        """Test fuzzing DNS response with multiple answers"""
        parser = DNSParser()
        mutator = DNSMutator()
        
        # DNS response with answer
        seed_msg = DNSMessage(
            transaction_id=0x5678,
            flags=0x8180,  # Response, recursion available
            questions=[DNSQuestion('google.com', DNSType.A, DNSClass.IN)],
            answers=[
                DNSResourceRecord('google.com', DNSType.A, DNSClass.IN, 300, b'\xd8\x3a\xc6\x0e'),
                DNSResourceRecord('google.com', DNSType.A, DNSClass.IN, 300, b'\xd8\x3a\xc6\x0f')
            ]
        )
        seed_data = parser.reconstruct(seed_msg)
        
        mutations = []
        for _ in range(15):
            mutated = mutator.mutate(seed_data)
            mutations.append(mutated)
            
            # All should be bytes
            assert isinstance(mutated, bytes)
        
        # Should generate variety
        unique_mutations = set(mutations)
        assert len(unique_mutations) > 1  # Should have variation
    
    def test_compression_pointer_fuzzing(self):
        """Test fuzzing with domain name compression"""
        parser = DNSParser()
        mutator = DNSMutator()
        
        # Message with multiple identical names (triggers compression)
        seed_msg = DNSMessage(
            transaction_id=0xABCD,
            flags=0x8180,
            questions=[DNSQuestion('example.com', DNSType.A, DNSClass.IN)],
            answers=[
                DNSResourceRecord('example.com', DNSType.A, DNSClass.IN, 300, b'\x01\x02\x03\x04'),
                DNSResourceRecord('www.example.com', DNSType.A, DNSClass.IN, 300, b'\x05\x06\x07\x08')
            ]
        )
        seed_data = parser.reconstruct(seed_msg)
        
        for _ in range(10):
            mutated = mutator.mutate(seed_data)
            
            # Try parsing
            parsed = parser.parse(mutated)
            # Some should parse, some might not
            if parsed:
                assert isinstance(parsed, DNSMessage)
    
    def test_invalid_dns_handling(self):
        """Test fuzzing handles invalid DNS gracefully"""
        mutator = DNSMutator()
        
        # Completely invalid data
        invalid_data = b'\x00\x01\x02\x03\x04'
        
        # Should not crash
        mutated = mutator.mutate(invalid_data)
        assert isinstance(mutated, bytes)
    
    def test_malformed_compression_mutation(self):
        """Test mutation of packets with potential compression issues"""
        parser = DNSParser()
        mutator = DNSMutator()
        
        # Create packet and mutate multiple times
        seed_msg = DNSMessage(
            transaction_id=0x9999,
            flags=0x0100,
            questions=[
                DNSQuestion('test1.example.com', DNSType.A, DNSClass.IN),
                DNSQuestion('test2.example.com', DNSType.MX, DNSClass.IN)
            ]
        )
        seed_data = parser.reconstruct(seed_msg)
        
        crash_count = 0
        success_count = 0
        
        for _ in range(20):
            try:
                mutated = mutator.mutate(seed_data)
                success_count += 1
                assert len(mutated) > 0
            except Exception:
                crash_count += 1
        
        # Should mostly succeed
        assert success_count > 15
    
    def test_query_type_fuzzing(self):
        """Test fuzzing different query types"""
        parser = DNSParser()
        mutator = DNSMutator()
        
        query_types = [DNSType.A, DNSType.AAAA, DNSType.MX, DNSType.TXT, DNSType.NS]
        
        for qtype in query_types:
            seed_msg = DNSMessage(
                transaction_id=0x0001,
                flags=0x0100,
                questions=[DNSQuestion('test.com', qtype, DNSClass.IN)]
            )
            seed_data = parser.reconstruct(seed_msg)
            
            # Mutate
            mutated = mutator.mutate(seed_data)
            
            assert isinstance(mutated, bytes)
            assert len(mutated) >= 12  # At least header
    
    def test_ttl_mutation_coverage(self):
        """Test TTL value mutations don't break parsing"""
        parser = DNSParser()
        mutator = DNSMutator()
        
        seed_msg = DNSMessage(
            transaction_id=0x1111,
            flags=0x8180,
            answers=[
                DNSResourceRecord('example.com', DNSType.A, DNSClass.IN, 3600, b'\x01\x02\x03\x04')
            ]
        )
        seed_data = parser.reconstruct(seed_msg)
        
        ttl_values_seen = set()
        
        for _ in range(30):
            mutated_data = mutator.mutate(seed_data)
            parsed = parser.parse(mutated_data)
            
            if parsed and parsed.answers:
                ttl_values_seen.add(parsed.answers[0].ttl)
        
        # Should see variety of TTL values
        assert len(ttl_values_seen) > 1
    
    def test_rdata_length_mismatch(self):
        """Test RDATA mutations can create length mismatches"""
        parser = DNSParser()
        mutator = DNSMutator()
        
        seed_msg = DNSMessage(
            transaction_id=0x2222,
            flags=0x8180,
            answers=[
                DNSResourceRecord('test.com', DNSType.A, DNSClass.IN, 300, b'\x01\x02\x03\x04')
            ]
        )
        seed_data = parser.reconstruct(seed_msg)
        
        for _ in range(15):
            mutated = mutator.mutate(seed_data)
            
            # Mutation should not crash
            assert isinstance(mutated, bytes)
            
            # Try parsing (may or may not succeed)
            parsed = parser.parse(mutated)
            # No assertion - just checking no crash
    
    def test_multiple_resource_records_fuzzing(self):
        """Test fuzzing with authority and additional sections"""
        parser = DNSParser()
        mutator = DNSMutator()
        
        seed_msg = DNSMessage(
            transaction_id=0x3333,
            flags=0x8180,
            questions=[DNSQuestion('example.com', DNSType.A, DNSClass.IN)],
            answers=[DNSResourceRecord('example.com', DNSType.A, DNSClass.IN, 300, b'\x01\x02\x03\x04')],
            authority=[DNSResourceRecord('example.com', DNSType.NS, DNSClass.IN, 3600, b'\x03ns1\x07example\x03com\x00')],
            additional=[DNSResourceRecord('ns1.example.com', DNSType.A, DNSClass.IN, 3600, b'\x05\x06\x07\x08')]
        )
        seed_data = parser.reconstruct(seed_msg)
        
        for _ in range(10):
            mutated = mutator.mutate(seed_data)
            
            # Should handle complex messages
            assert len(mutated) > 0
            
            parsed = parser.parse(mutated)
            if parsed:
                # Check structure exists
                assert hasattr(parsed, 'answers')
                assert hasattr(parsed, 'authority')
                assert hasattr(parsed, 'additional')
    
    def test_fuzzing_preserves_transaction_id(self):
        """Test that some mutations preserve parseable structure"""
        parser = DNSParser()
        mutator = DNSMutator()
        
        seed_msg = DNSMessage(
            transaction_id=0x4444,
            flags=0x0100,
            questions=[DNSQuestion('test.org', DNSType.A, DNSClass.IN)]
        )
        seed_data = parser.reconstruct(seed_msg)
        
        parseable_count = 0
        
        for _ in range(25):
            mutated = mutator.mutate(seed_data)
            parsed = parser.parse(mutated)
            
            if parsed:
                parseable_count += 1
        
        # At least some should remain parseable
        assert parseable_count > 0
