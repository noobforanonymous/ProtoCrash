# Protocol Parser Interfaces - Specification

## Overview

Protocol parsers provide structure-aware fuzzing for different protocols. Each parser understands the protocol format and enables targeted mutations.

---

## Base Parser Interface

### ProtocolParser (Abstract Base Class)

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ProtocolType(Enum):
    """Supported protocol types"""
    HTTP = "http"
    DNS = "dns"
    SMTP = "smtp"
    BINARY = "binary"
    CUSTOM = "custom"

@dataclass
class ParsedMessage:
    """Parsed protocol message structure"""
    protocol: ProtocolType
    fields: Dict[str, Any]
    raw_data: bytes
    valid: bool
    errors: List[str]

class ProtocolParser(ABC):
    """Base interface for all protocol parsers"""
    
    @abstractmethod
    def parse(self, data: bytes) -> ParsedMessage:
        """
        Parse raw data into structured message
        
        Args:
            data: Raw protocol data
            
        Returns:
            ParsedMessage with extracted fields
        """
        pass
    
    @abstractmethod
    def generate(self, template: Dict) -> bytes:
        """
        Generate protocol message from template
        
        Args:
            template: Message template with field values
            
        Returns:
            Raw protocol bytes
        """
        pass
    
    @abstractmethod
    def mutate_field(self, data: bytes, field_name: str, mutation: Any) -> bytes:
        """
        Mutate specific protocol field
        
        Args:
            data: Original protocol data
            field_name: Name of field to mutate
            mutation: New value for field
            
        Returns:
            Mutated protocol data
        """
        pass
    
    @abstractmethod
    def get_fields(self, data: bytes) -> List[str]:
        """Get list of mutable fields in message"""
        pass
    
    @abstractmethod
    def validate(self, data: bytes) -> bool:
        """Check if data is valid for this protocol"""
        pass
```

---

## HTTP Protocol Parser

```python
from urllib.parse import urlparse
import re

class HTTPParser(ProtocolParser):
    """HTTP/1.x protocol parser"""
    
    HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH', 'TRACE']
    HTTP_VERSIONS = ['HTTP/1.0', 'HTTP/1.1', 'HTTP/2.0']
    
    def parse(self, data: bytes) -> ParsedMessage:
        """Parse HTTP request/response"""
        try:
            text = data.decode('utf-8', errors='ignore')
            lines = text.split('\r\n')
            
            # Parse request line
            request_line = lines[0].split()
            if len(request_line) < 3:
                return ParsedMessage(
                    protocol=ProtocolType.HTTP,
                    fields={},
                    raw_data=data,
                    valid=False,
                    errors=['Invalid request line']
                )
            
            fields = {
                'method': request_line[0],
                'path': request_line[1],
                'version': request_line[2],
                'headers': {},
                'body': ''
            }
            
            # Parse headers
            i = 1
            while i < len(lines) and lines[i]:
                if ':' in lines[i]:
                    key, value = lines[i].split(':', 1)
                    fields['headers'][key.strip()] = value.strip()
                i += 1
            
            # Parse body
            if i + 1 < len(lines):
                fields['body'] = '\r\n'.join(lines[i+1:])
            
            return ParsedMessage(
                protocol=ProtocolType.HTTP,
                fields=fields,
                raw_data=data,
                valid=True,
                errors=[]
            )
            
        except Exception as e:
            return ParsedMessage(
                protocol=ProtocolType.HTTP,
                fields={},
                raw_data=data,
                valid=False,
                errors=[str(e)]
            )
    
    def generate(self, template: Dict) -> bytes:
        """Generate HTTP request from template"""
        method = template.get('method', 'GET')
        path = template.get('path', '/')
        version = template.get('version', 'HTTP/1.1')
        headers = template.get('headers', {})
        body = template.get('body', '')
        
        # Build request line
        request = f"{method} {path} {version}\r\n"
        
        # Add headers
        for key, value in headers.items():
            request += f"{key}: {value}\r\n"
        
        # Empty line before body
        request += "\r\n"
        
        # Add body
        if body:
            request += body
        
        return request.encode('utf-8')
    
    def mutate_field(self, data: bytes, field_name: str, mutation: Any) -> bytes:
        """Mutate HTTP field"""
        parsed = self.parse(data)
        
        if not parsed.valid:
            return data
        
        if field_name == 'method':
            parsed.fields['method'] = mutation
        elif field_name == 'path':
            parsed.fields['path'] = mutation
        elif field_name == 'version':
            parsed.fields['version'] = mutation
        elif field_name == 'body':
            parsed.fields['body'] = mutation
        elif field_name.startswith('header:'):
            header_name = field_name.split(':', 1)[1]
            parsed.fields['headers'][header_name] = mutation
        
        return self.generate(parsed.fields)
    
    def get_fields(self, data: bytes) -> List[str]:
        """Get mutable HTTP fields"""
        parsed = self.parse(data)
        if not parsed.valid:
            return []
        
        fields = ['method', 'path', 'version', 'body']
        
        # Add header fields
        for header in parsed.fields.get('headers', {}).keys():
            fields.append(f'header:{header}')
        
        return fields
    
    def validate(self, data: bytes) -> bool:
        """Validate HTTP request"""
        parsed = self.parse(data)
        return parsed.valid and parsed.fields['method'] in self.HTTP_METHODS
```

---

## DNS Protocol Parser

```python
import struct

class DNSParser(ProtocolParser):
    """DNS protocol parser"""
    
    QUERY_TYPES = {
        1: 'A', 2: 'NS', 5: 'CNAME', 6: 'SOA', 12: 'PTR',
        15: 'MX', 16: 'TXT', 28: 'AAAA', 255: 'ANY'
    }
    
    def parse(self, data: bytes) -> ParsedMessage:
        """Parse DNS packet"""
        if len(data) < 12:
            return ParsedMessage(
                protocol=ProtocolType.DNS,
                fields={},
                raw_data=data,
                valid=False,
                errors=['Packet too short']
            )
        
        try:
            # Parse header (12 bytes)
            transaction_id, flags, qdcount, ancount, nscount, arcount = struct.unpack('!HHHHHH', data[:12])
            
            fields = {
                'transaction_id': transaction_id,
                'flags': flags,
                'questions': qdcount,
                'answers': ancount,
                'authority': nscount,
                'additional': arcount,
                'query_name': self._parse_name(data, 12),
            }
            
            # Parse query type and class
            name_len = len(self._encode_name(fields['query_name']))
            if len(data) >= 12 + name_len + 4:
                qtype, qclass = struct.unpack('!HH', data[12+name_len:12+name_len+4])
                fields['query_type'] = self.QUERY_TYPES.get(qtype, qtype)
                fields['query_class'] = qclass
            
            return ParsedMessage(
                protocol=ProtocolType.DNS,
                fields=fields,
                raw_data=data,
                valid=True,
                errors=[]
            )
            
        except Exception as e:
            return ParsedMessage(
                protocol=ProtocolType.DNS,
                fields={},
                raw_data=data,
                valid=False,
                errors=[str(e)]
            )
    
    def generate(self, template: Dict) -> bytes:
        """Generate DNS query"""
        tid = template.get('transaction_id', 0x1234)
        flags = template.get('flags', 0x0100)  # Standard query
        query_name = template.get('query_name', 'example.com')
        qtype = template.get('query_type', 1)  # A record
        qclass = template.get('query_class', 1)  # IN
        
        # Build header
        packet = struct.pack('!HHHHHH', tid, flags, 1, 0, 0, 0)
        
        # Add query name
        packet += self._encode_name(query_name)
        
        # Add query type and class
        packet += struct.pack('!HH', qtype, qclass)
        
        return packet
    
    def mutate_field(self, data: bytes, field_name: str, mutation: Any) -> bytes:
        """Mutate DNS field"""
        parsed = self.parse(data)
        if not parsed.valid:
            return data
        
        parsed.fields[field_name] = mutation
        return self.generate(parsed.fields)
    
    def get_fields(self, data: bytes) -> List[str]:
        """Get mutable DNS fields"""
        return ['transaction_id', 'flags', 'query_name', 'query_type', 'query_class']
    
    def validate(self, data: bytes) -> bool:
        """Validate DNS packet"""
        parsed = self.parse(data)
        return parsed.valid and len(data) >= 12
    
    def _parse_name(self, data: bytes, offset: int) -> str:
        """Parse DNS name from packet"""
        labels = []
        pos = offset
        
        while pos < len(data):
            length = data[pos]
            if length == 0:
                break
            if length >= 192:  # Compression pointer
                break
            
            pos += 1
            if pos + length <= len(data):
                labels.append(data[pos:pos+length].decode('ascii', errors='ignore'))
                pos += length
        
        return '.'.join(labels)
    
    def _encode_name(self, name: str) -> bytes:
        """Encode DNS name"""
        encoded = b''
        for label in name.split('.'):
            encoded += bytes([len(label)]) + label.encode('ascii')
        encoded += b'\x00'
        return encoded
```

---

## SMTP Protocol Parser

```python
class SMTPParser(ProtocolParser):
    """SMTP protocol parser"""
    
    COMMANDS = ['HELO', 'EHLO', 'MAIL FROM', 'RCPT TO', 'DATA', 'QUIT', 'RSET', 'HELP']
    
    def parse(self, data: bytes) -> ParsedMessage:
        """Parse SMTP command"""
        try:
            text = data.decode('utf-8', errors='ignore').strip()
            parts = text.split(None, 1)
            
            fields = {
                'command': parts[0] if parts else '',
                'arguments': parts[1] if len(parts) > 1 else '',
                'raw': text
            }
            
            return ParsedMessage(
                protocol=ProtocolType.SMTP,
                fields=fields,
                raw_data=data,
                valid=True,
                errors=[]
            )
            
        except Exception as e:
            return ParsedMessage(
                protocol=ProtocolType.SMTP,
                fields={},
                raw_data=data,
                valid=False,
                errors=[str(e)]
            )
    
    def generate(self, template: Dict) -> bytes:
        """Generate SMTP command"""
        command = template.get('command', 'HELO')
        arguments = template.get('arguments', 'localhost')
        
        if arguments:
            smtp_cmd = f"{command} {arguments}\r\n"
        else:
            smtp_cmd = f"{command}\r\n"
        
        return smtp_cmd.encode('utf-8')
    
    def mutate_field(self, data: bytes, field_name: str, mutation: Any) -> bytes:
        """Mutate SMTP field"""
        parsed = self.parse(data)
        if not parsed.valid:
            return data
        
        parsed.fields[field_name] = mutation
        return self.generate(parsed.fields)
    
    def get_fields(self, data: bytes) -> List[str]:
        """Get mutable SMTP fields"""
        return ['command', 'arguments']
    
    def validate(self, data: bytes) -> bool:
        """Validate SMTP command"""
        parsed = self.parse(data)
        return parsed.valid
```

---

## Binary Protocol Parser

```python
from typing import List, Dict

@dataclass
class BinaryField:
    """Binary protocol field definition"""
    name: str
    type: str  # 'uint8', 'uint16', 'uint32', 'bytes', 'string'
    offset: int
    size: Optional[int] = None
    computed: Optional[str] = None  # For length/checksum fields

class BinaryProtocolParser(ProtocolParser):
    """Generic binary protocol parser using grammar"""
    
    def __init__(self, grammar: Dict):
        """
        Initialize with protocol grammar
        
        Grammar format:
        {
            "name": "CustomProtocol",
            "fields": [
                {"name": "magic", "type": "uint32", "value": 0xDEADBEEF},
                {"name": "length", "type": "uint16", "computed": "len(payload)"},
                {"name": "payload", "type": "bytes", "max_length": 1024}
            ]
        }
        """
        self.grammar = grammar
        self.fields = self._parse_grammar(grammar)
    
    def parse(self, data: bytes) -> ParsedMessage:
        """Parse binary message using grammar"""
        fields = {}
        offset = 0
        
        for field_def in self.fields:
            if offset >= len(data):
                break
            
            if field_def.type == 'uint8':
                fields[field_def.name] = data[offset]
                offset += 1
            elif field_def.type == 'uint16':
                fields[field_def.name] = struct.unpack('<H', data[offset:offset+2])[0]
                offset += 2
            elif field_def.type == 'uint32':
                fields[field_def.name] = struct.unpack('<I', data[offset:offset+4])[0]
                offset += 4
            elif field_def.type == 'bytes':
                size = field_def.size or (len(data) - offset)
                fields[field_def.name] = data[offset:offset+size]
                offset += size
        
        return ParsedMessage(
            protocol=ProtocolType.BINARY,
            fields=fields,
            raw_data=data,
            valid=True,
            errors=[]
        )
    
    def generate(self, template: Dict) -> bytes:
        """Generate binary message from template"""
        packet = b''
        
        for field_def in self.fields:
            value = template.get(field_def.name, 0)
            
            if field_def.type == 'uint8':
                packet += struct.pack('B', value)
            elif field_def.type == 'uint16':
                packet += struct.pack('<H', value)
            elif field_def.type == 'uint32':
                packet += struct.pack('<I', value)
            elif field_def.type == 'bytes':
                packet += value if isinstance(value, bytes) else b''
        
        return packet
    
    def mutate_field(self, data: bytes, field_name: str, mutation: Any) -> bytes:
        """Mutate binary field"""
        parsed = self.parse(data)
        parsed.fields[field_name] = mutation
        return self.generate(parsed.fields)
    
    def get_fields(self, data: bytes) -> List[str]:
        """Get mutable fields from grammar"""
        return [f.name for f in self.fields]
    
    def validate(self, data: bytes) -> bool:
        """Validate binary message"""
        parsed = self.parse(data)
        return parsed.valid
    
    def _parse_grammar(self, grammar: Dict) -> List[BinaryField]:
        """Parse grammar into field definitions"""
        fields = []
        offset = 0
        
        for field in grammar.get('fields', []):
            size = {
                'uint8': 1,
                'uint16': 2,
                'uint32': 4,
            }.get(field['type'])
            
            fields.append(BinaryField(
                name=field['name'],
                type=field['type'],
                offset=offset,
                size=size,
                computed=field.get('computed')
            ))
            
            if size:
                offset += size
        
        return fields
```

---

## Protocol Auto-Detection

```python
class ProtocolDetector:
    """Auto-detect protocol type from data"""
    
    @staticmethod
    def detect(data: bytes) -> ProtocolType:
        """Detect protocol from data"""
        
        # Try HTTP
        if data.startswith(b'GET ') or data.startswith(b'POST ') or data.startswith(b'HTTP/'):
            return ProtocolType.HTTP
        
        # Try SMTP
        smtp_commands = [b'HELO', b'EHLO', b'MAIL FROM', b'RCPT TO']
        if any(data.startswith(cmd) for cmd in smtp_commands):
            return ProtocolType.SMTP
        
        # Try DNS (12-byte header)
        if len(data) >= 12:
            try:
                # Check if it looks like DNS
                flags = struct.unpack('!H', data[2:4])[0]
                if flags & 0x8000 or flags & 0x0100:  # Response or query flags
                    return ProtocolType.DNS
            except:
                pass
        
        # Default to binary
        return ProtocolType.BINARY
```

---

## Parser Factory

```python
class ParserFactory:
    """Factory for creating protocol parsers"""
    
    _parsers = {
        ProtocolType.HTTP: HTTPParser,
        ProtocolType.DNS: DNSParser,
        ProtocolType.SMTP: SMTPParser,
    }
    
    @classmethod
    def create(cls, protocol: ProtocolType, **kwargs) -> ProtocolParser:
        """Create parser for protocol type"""
        
        if protocol == ProtocolType.BINARY:
            if 'grammar' not in kwargs:
                raise ValueError("Binary protocol requires grammar")
            return BinaryProtocolParser(kwargs['grammar'])
        
        parser_class = cls._parsers.get(protocol)
        if not parser_class:
            raise ValueError(f"Unsupported protocol: {protocol}")
        
        return parser_class()
    
    @classmethod
    def auto_create(cls, data: bytes) -> ProtocolParser:
        """Auto-detect and create parser"""
        protocol = ProtocolDetector.detect(data)
        return cls.create(protocol)
```

---

Status: Protocol parser interfaces specification complete
