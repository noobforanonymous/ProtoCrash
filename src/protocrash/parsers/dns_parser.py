"""
DNS Protocol Parser (RFC 1035)
"""
import struct
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from ..core.protocol_parser import ProtocolParser, ProtocolMessage
from ..core.protocol_registry import ProtocolRegistry
# DNS Query Types
class DNSType:
    """DNS query type constants (RFC 1035)"""
    A = 1          # IPv4 address
    NS = 2         # Name server
    CNAME = 5      # Canonical name
    SOA = 6        # Start of authority
    PTR = 12       # Pointer
    MX = 15        # Mail exchange
    TXT = 16       # Text
    AAAA = 28      # IPv6 address
    ANY = 255      # All records
# DNS Classes
class DNSClass:
    """DNS class constants (RFC 1035)"""
    IN = 1         # Internet
    CS = 2         # CSNET (obsolete)
    CH = 3         # CHAOS
    HS = 4         # Hesiod
@dataclass
class DNSQuestion:
    """DNS question section entry"""
    name: str
    qtype: int
    qclass: int
@dataclass
class DNSResourceRecord:
    """DNS resource record (answer/authority/additional)"""
    name: str
    rtype: int
    rclass: int
    ttl: int
    rdata: bytes
@dataclass
class DNSMessage(ProtocolMessage):
    """DNS message structure"""
    transaction_id: int = 0
    flags: int = 0
    questions: List[DNSQuestion] = field(default_factory=list)
    answers: List[DNSResourceRecord] = field(default_factory=list)
    authority: List[DNSResourceRecord] = field(default_factory=list)
    additional: List[DNSResourceRecord] = field(default_factory=list)
    # Flag accessors
    @property
    def is_response(self) -> bool:
        """Check if message is a response (vs query)"""
        return (self.flags >> 15) & 1 == 1
    @property
    def opcode(self) -> int:
        """Get operation code from flags"""
        return (self.flags >> 11) & 0x0F
    @property
    def rcode(self) -> int:
        """Get response code from flags"""
        return self.flags & 0x0F
@ProtocolRegistry.register("dns")
class DNSParser(ProtocolParser):
    """DNS protocol parser"""
    @property
    def protocol_name(self) -> str:
        return "dns"
    def parse(self, data: bytes) -> Optional[DNSMessage]:
        """
        Parse DNS message
        Args:
            data: Raw DNS packet
        Returns:
            DNSMessage or None if invalid
        """
        try:
            if len(data) < 12:  # Minimum header size
                return None
            # Parse header
            header = struct.unpack('!HHHHHH', data[:12])
            transaction_id, flags, qdcount, ancount, nscount, arcount = header
            offset = 12
            msg = DNSMessage(
                transaction_id=transaction_id,
                flags=flags,
                raw_data=data
            )
            # Parse questions
            for _ in range(qdcount):
                name, offset = self._parse_name(data, offset)
                if offset + 4 > len(data):
                    return None
                qtype, qclass = struct.unpack('!HH', data[offset:offset+4])
                offset += 4
                msg.questions.append(DNSQuestion(name, qtype, qclass))
            # Parse answers
            for _ in range(ancount):
                rr, offset = self._parse_rr(data, offset)
                if not rr:
                    return None
                msg.answers.append(rr)
            # Parse authority
            for _ in range(nscount):
                rr, offset = self._parse_rr(data, offset)
                if not rr:
                    return None
                msg.authority.append(rr)
            # Parse additional
            for _ in range(arcount):
                rr, offset = self._parse_rr(data, offset)
                if not rr:
                    return None
                msg.additional.append(rr)
            return msg
        except (struct.error, IndexError):
            return None
    def _parse_name(self, data: bytes, offset: int) -> Tuple[str, int]:
        """
        Parse DNS domain name with compression support
        Args:
            data: Full DNS packet
            offset: Current offset
        Returns:
            (domain_name, new_offset)
        """
        labels = []
        jump_performed = False
        original_offset = offset
        max_jumps = 10
        jumps = 0
        while True:
            if offset >= len(data):
                break
            length = data[offset]
            # Check for compression (pointer)
            if (length & 0xC0) == 0xC0:
                if offset + 1 >= len(data):
                    break
                # Pointer: 2 bytes (14-bit offset)
                pointer = struct.unpack('!H', data[offset:offset+2])[0]
                pointer &= 0x3FFF  # Remove top 2 bits
                if not jump_performed:
                    original_offset = offset + 2
                    jump_performed = True
                offset = pointer
                jumps += 1
                if jumps > max_jumps:  # Prevent infinite loops
                    break
                continue
            # End of name
            if length == 0:
                offset += 1
                break
            # Regular label
            if offset + 1 + length > len(data):
                break
            label = data[offset+1:offset+1+length].decode('utf-8', errors='ignore')
            labels.append(label)
            offset += 1 + length
        domain = '.'.join(labels) if labels else '.'
        return domain, original_offset if jump_performed else offset
    def _parse_rr(self, data: bytes, offset: int) -> Tuple[Optional[DNSResourceRecord], int]:
        """
        Parse resource record
        Args:
            data: Full DNS packet
            offset: Current offset
        Returns:
            (DNSResourceRecord, new_offset) or (None, offset) if error
        """
        try:
            # Parse name
            name, offset = self._parse_name(data, offset)
            if offset + 10 > len(data):
                return None, offset
            # Parse type, class, TTL, rdlength
            rtype, rclass, ttl, rdlength = struct.unpack('!HHIH', data[offset:offset+10])
            offset += 10
            if offset + rdlength > len(data):
                return None, offset
            # Extract rdata
            rdata = data[offset:offset+rdlength]
            offset += rdlength
            return DNSResourceRecord(name, rtype, rclass, ttl, rdata), offset
        except (struct.error, IndexError):
            return None, offset
    def reconstruct(self, message: DNSMessage) -> bytes:
        """
        Reconstruct DNS message to bytes
        Args:
            message: DNSMessage object
        Returns:
            Raw DNS packet
        """
        # Build header
        header = struct.pack(
            '!HHHHHH',
            message.transaction_id,
            message.flags,
            len(message.questions),
            len(message.answers),
            len(message.authority),
            len(message.additional)
        )
        result = bytearray(header)
        # Build questions
        for q in message.questions:
            result.extend(self._build_name(q.name))
            result.extend(struct.pack('!HH', q.qtype, q.qclass))
        # Build answers
        for rr in message.answers:
            result.extend(self._build_rr(rr))
        # Build authority
        for rr in message.authority:
            result.extend(self._build_rr(rr))
        # Build additional
        for rr in message.additional:
            result.extend(self._build_rr(rr))
        return bytes(result)
    def _build_name(self, name: str) -> bytes:
        """
        Build DNS name in label format
        Args:
            name: Domain name (e.g., "www.example.com")
        Returns:
            DNS label format
        """
        if name in ('.', ''):
            return b'\x00'
        result = bytearray()
        labels = name.split('.')
        for label in labels:
            if label:  # Skip empty labels
                label_bytes = label.encode('utf-8')
                result.append(len(label_bytes))
                result.extend(label_bytes)
        result.append(0)  # Null terminator
        return bytes(result)
    def _build_rr(self, rr: DNSResourceRecord) -> bytes:
        """
        Build resource record
        Args:
            rr: DNSResourceRecord object
        Returns:
            Resource record bytes
        """
        result = bytearray()
        result.extend(self._build_name(rr.name))
        result.extend(struct.pack('!HHIH', rr.rtype, rr.rclass, rr.ttl, len(rr.rdata)))
        result.extend(rr.rdata)
        return bytes(result)
    def detect(self, data: bytes, port: Optional[int] = None) -> float:
        """
        Detect if data is DNS protocol
        Args:
            data: Raw data
            port: Optional port hint
        Returns:
            Confidence 0.0-1.0
        """
        confidence = 0.0
        # Port hint
        if port == 53:
            confidence += 0.3
        # Check minimum size
        if len(data) < 12:
            return 0.0
        try:
            # Parse header
            header = struct.unpack('!HHHHHH', data[:12])
            tid, flags, qdcount, ancount, nscount, arcount = header
            # Check flags are reasonable
            qr = (flags >> 15) & 1  # Query/Response
            opcode = (flags >> 11) & 0x0F
            rcode = flags & 0x0F
            # Opcode should be 0-2 usually
            if opcode > 5:
                return confidence * 0.5
            # RCODE should be 0-5 usually
            if rcode > 5:
                return confidence * 0.5
            # Questions should be reasonable (<20)
            if qdcount > 20 or ancount > 100:
                return confidence * 0.5
            confidence += 0.4
            # Try to parse a question
            if qdcount > 0:
                try:
                    name, offset = self._parse_name(data, 12)
                    if offset < len(data) and len(name) > 0:
                        confidence += 0.3
                except:
                    pass
        except (struct.error, IndexError):
            return 0.0
        return min(1.0, confidence)
