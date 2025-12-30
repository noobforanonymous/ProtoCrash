"""
DNS-specific mutation strategies
"""
import random
from ..parsers.dns_parser import DNSParser, DNSMessage, DNSQuestion, DNSResourceRecord, DNSType, DNSClass
class DNSMutator:
    """DNS protocol-specific mutator"""
    def __init__(self):
        self.parser = DNSParser()
        # Interesting DNS values
        self.interesting_qtypes = [
            DNSType.A, DNSType.NS, DNSType.CNAME, DNSType.SOA,
            DNSType.PTR, DNSType.MX, DNSType.TXT, DNSType.AAAA,
            DNSType.ANY, 0, 65535, 999, 1234  # Valid + invalid types
        ]
        self.interesting_flags = [
            0x0000,  # Standard query
            0x8000,  # Response
            0x0100,  # Recursion desired
            0x8180,  # Standard response
            0xFFFF,  # All flags set
            0x7800,  # Opcode bits set
        ]
    def mutate(self, data: bytes) -> bytes:
        """
        Main mutation entry point
        Args:
            data: DNS message bytes
        Returns:
            Mutated DNS message
        """
        # Try to parse as DNS
        msg = self.parser.parse(data)
        if not msg:
            # Not valid DNS, return basic mutation
            return self._mutate_raw(data)
        # Select random mutation strategy
        strategies = [
            self.mutate_header_flags,
            self.mutate_question_section,
            self.mutate_answer_section,
            self.mutate_domain_names,
            self.mutate_ttl_values,
            self.mutate_rdata,
        ]
        strategy = random.choice(strategies)
        mutated_msg = strategy(msg)
        return self.parser.reconstruct(mutated_msg)
    def mutate_header_flags(self, msg: DNSMessage) -> DNSMessage:
        """Mutate DNS header flags"""
        mutation_type = random.choice(['flip_bit', 'set_interesting', 'corrupt'])
        if mutation_type == 'flip_bit':
            # Flip random bit in flags
            bit_position = random.randint(0, 15)
            msg.flags ^= (1 << bit_position)
        elif mutation_type == 'set_interesting':
            # Set to interesting value
            msg.flags = random.choice(self.interesting_flags)
        else:  # corrupt
            # Corrupt specific flag fields
            qr = random.randint(0, 1)
            opcode = random.randint(0, 15)  # Usually 0-2
            aa = random.randint(0, 1)
            tc = random.randint(0, 1)
            rd = random.randint(0, 1)
            ra = random.randint(0, 1)
            z = random.randint(0, 7)  # Usually 0
            rcode = random.randint(0, 15)  # Usually 0-5
            msg.flags = (
                (qr << 15) |
                (opcode << 11) |
                (aa << 10) |
                (tc << 9) |
                (rd << 8) |
                (ra << 7) |
                (z << 4) |
                rcode
            )
        return msg
    def mutate_question_section(self, msg: DNSMessage) -> DNSMessage:
        """Mutate question section"""
        if not msg.questions:
            # Add a question if none exist
            msg.questions.append(
                DNSQuestion('test.com', DNSType.A, DNSClass.IN)
            )
            return msg
        question = random.choice(msg.questions)
        mutation_type = random.choice(['qtype', 'qclass', 'qname'])
        if mutation_type == 'qtype':
            # Mutate query type
            question.qtype = random.choice(self.interesting_qtypes)
        elif mutation_type == 'qclass':
            # Mutate query class
            question.qclass = random.choice([
                DNSClass.IN, DNSClass.CS, DNSClass.CH, DNSClass.HS,
                0, 255, 65535  # Invalid values
            ])
        else:  # qname
            # Mutate domain name
            question.name = self._mutate_domain_name(question.name)
        return msg
    def mutate_answer_section(self, msg: DNSMessage) -> DNSMessage:
        """Mutate answer section"""
        if not msg.answers:
            # Optionally add a fake answer
            if random.random() < 0.3:
                msg.answers.append(
                    DNSResourceRecord(
                        'example.com',
                        DNSType.A,
                        DNSClass.IN,
                        300,
                        b'\x01\x02\x03\x04'
                    )
                )
            return msg
        rr = random.choice(msg.answers)
        mutation_type = random.choice(['rtype', 'rclass', 'rname'])
        if mutation_type == 'rtype':
            rr.rtype = random.choice(self.interesting_qtypes)
        elif mutation_type == 'rclass':
            rr.rclass = random.choice([1, 2, 3, 4, 0, 255, 65535])
        else:  # rname
            rr.name = self._mutate_domain_name(rr.name)
        return msg
    def mutate_domain_names(self, msg: DNSMessage) -> DNSMessage:
        """Mutate all domain names in message"""
        # Mutate question names
        for q in msg.questions:
            if random.random() < 0.5:
                q.name = self._mutate_domain_name(q.name)
        # Mutate answer names
        for rr in msg.answers:
            if random.random() < 0.3:
                rr.name = self._mutate_domain_name(rr.name)
        return msg
    def mutate_ttl_values(self, msg: DNSMessage) -> DNSMessage:
        """Mutate TTL values in resource records"""
        interesting_ttls = [0, 1, 60, 300, 3600, 86400, 0xFFFFFFFF]
        for rr in msg.answers + msg.authority + msg.additional:
            mutation_type = random.choice(['set_interesting', 'arithmetic', 'random'])
            if mutation_type == 'set_interesting':
                rr.ttl = random.choice(interesting_ttls)
            elif mutation_type == 'arithmetic':
                rr.ttl = max(0, min(0xFFFFFFFF, rr.ttl + random.choice([-1000, -100, -1, 1, 100, 1000])))
            else:  # random
                rr.ttl = random.randint(0, 0xFFFFFFFF)
        return msg
    def mutate_rdata(self, msg: DNSMessage) -> DNSMessage:
        """Mutate resource record data"""
        all_rrs = msg.answers + msg.authority + msg.additional
        if not all_rrs:
            return msg
        rr = random.choice(all_rrs)
        mutation_type = random.choice(['truncate', 'extend', 'flip_bytes', 'zero'])
        if mutation_type == 'truncate' and len(rr.rdata) > 1:
            # Truncate rdata
            new_len = random.randint(0, len(rr.rdata) - 1)
            rr.rdata = rr.rdata[:new_len]
        elif mutation_type == 'extend':
            # Extend rdata with random bytes
            extra = random.randint(1, 100)
            rr.rdata += bytes(random.randint(0, 255) for _ in range(extra))
        elif mutation_type == 'flip_bytes':
            # Flip random bytes
            data = bytearray(rr.rdata)
            for _ in range(min(5, len(data))):
                if data:
                    pos = random.randint(0, len(data) - 1)
                    data[pos] ^= random.randint(1, 255)
            rr.rdata = bytes(data)
        else:  # zero
            # Zero out rdata
            rr.rdata = b'\x00' * len(rr.rdata)
        return msg
    def _mutate_domain_name(self, domain: str) -> str:
        """Mutate a single domain name"""
        mutation_type = random.choice([
            'add_label', 'remove_label', 'long_label',
            'invalid_chars', 'numeric', 'empty', 'repeat'
        ])
        if mutation_type == 'add_label':
            # Add extra label
            labels = domain.split('.')
            labels.insert(random.randint(0, len(labels)), 'x' * random.randint(1, 63))
            return '.'.join(labels)
        elif mutation_type == 'remove_label':
            # Remove a label
            labels = domain.split('.')
            if len(labels) > 1:
                labels.pop(random.randint(0, len(labels) - 1))
            return '.'.join(labels)
        elif mutation_type == 'long_label':
            # Create very long label (>63 chars violates RFC)
            labels = domain.split('.')
            if labels:
                idx = random.randint(0, len(labels) - 1)
                labels[idx] = 'a' * random.randint(64, 255)
            return '.'.join(labels)
        elif mutation_type == 'invalid_chars':
            # Add invalid characters
            chars = list(domain)
            if chars:
                for _ in range(min(3, len(chars))):
                    pos = random.randint(0, len(chars) - 1)
                    chars[pos] = random.choice(['@', '#', '$', '%', ' ', '\x00'])
            return ''.join(chars)
        elif mutation_type == 'numeric':
            # All numeric labels
            return '.'.join(str(random.randint(0, 255)) for _ in range(4))
        elif mutation_type == 'empty':
            # Empty labels (double dots)
            return domain.replace('.', '..')
        else:  # repeat
            # Repeat labels
            labels = domain.split('.')
            if labels:
                label = random.choice(labels)
                return '.'.join([label] * random.randint(5, 20))
        return domain
    def _mutate_raw(self, data: bytes) -> bytes:
        """Basic byte-level mutation for non-parseable data"""
        if len(data) < 12:
            # Too short for DNS header, just flip some bytes
            data = bytearray(data)
            if data:
                data[random.randint(0, len(data) - 1)] ^= 0xFF
            return bytes(data)
        # Mutate header fields directly
        data = bytearray(data)
        mutation_type = random.choice(['flags', 'counts', 'data'])
        if mutation_type == 'flags':
            # Mutate flags (bytes 2-3)
            data[2] = random.randint(0, 255)
            data[3] = random.randint(0, 255)
        elif mutation_type == 'counts':
            # Mutate record counts (bytes 4-11)
            for i in range(4, 12):
                if random.random() < 0.3:
                    data[i] = random.randint(0, 255)
        else:  # data
            # Mutate random bytes in data section
            if len(data) > 12:
                for _ in range(min(10, len(data) - 12)):
                    pos = random.randint(12, len(data) - 1)
                    data[pos] ^= random.randint(1, 255)
        return bytes(data)
