#!/usr/bin/env python3
"""
Simple DNS Server Target - For Fuzzing Demo

A deliberately vulnerable DNS server for testing ProtoCrash.
Contains intentional bugs for demonstration purposes.

SECURITY WARNING: This is intentionally vulnerable code.
DO NOT use in production. For testing only.
"""

import struct
import sys

def parse_dns_query(data: bytes) -> dict:
    """Parse DNS query - contains intentional bugs"""
    if len(data) < 12:
        raise ValueError("DNS packet too short")
    
    # Parse header
    transaction_id = struct.unpack('!H', data[0:2])[0]
    flags = struct.unpack('!H', data[2:4])[0]
    questions = struct.unpack('!H', data[4:6])[0]
    
    # BUG 1: No bounds checking on question count
    if questions > 100:
        # Simulate crash on too many questions
        arr = [0] * questions  # Memory exhaustion
    
    # Parse question
    offset = 12
    labels = []
    
    while offset < len(data):
        length = data[offset]
        
        # BUG 2: Integer overflow on length
        if length > 63:
            # Simulate crash on invalid label length
            raise OverflowError("Label too long")
        
        if length == 0:
            break
        
        offset += 1
        
        # BUG 3: No bounds checking
        if offset + length > len(data):
            raise IndexError("Buffer overflow")
        
        label = data[offset:offset + length]
        labels.append(label.decode('ascii', errors='ignore'))
        offset += length
    
    domain = '.'.join(labels)
    
    # BUG 4: Null domain crash
    if not domain:
        raise RuntimeError("Empty domain")
    
    return {
        'transaction_id': transaction_id,
        'domain': domain,
        'flags': flags
    }

def create_dns_response(query: dict) -> bytes:
    """Create DNS response"""
    # Simple A record response pointing to 127.0.0.1
    response = struct.pack('!H', query['transaction_id'])  # Transaction ID
    response += struct.pack('!H', 0x8180)  # Flags: response, no error
    response += struct.pack('!H', 1)  # Questions
    response += struct.pack('!H', 1)  # Answers
    response += struct.pack('!H', 0)  # Authority
    response += struct.pack('!H', 0)  # Additional
    
    # Encode domain in DNS format
    for label in query['domain'].split('.'):
        response += bytes([len(label)]) + label.encode()
    response += b'\x00'  # End of domain
    
    response += struct.pack('!H', 1)  # Type A
    response += struct.pack('!H', 1)  # Class IN
    
    # Answer
    response += b'\xc0\x0c'  # Pointer to domain
    response += struct.pack('!H', 1)  # Type A
    response += struct.pack('!H', 1)  # Class IN
    response += struct.pack('!I', 300)  # TTL
    response += struct.pack('!H', 4)  # RDLENGTH
    response += bytes([127, 0, 0, 1])  # RDATA (127.0.0.1)
    
    return response

def main():
    """Process DNS query from file or stdin"""
    if len(sys.argv) > 1:
        # File input mode for fuzzing
        with open(sys.argv[1], 'rb') as f:
            data = f.read()
    else:
        # Stdin mode
        data = sys.stdin.buffer.read()
    
    try:
        query = parse_dns_query(data)
        response = create_dns_response(query)
        sys.stdout.buffer.write(response)
    except Exception as e:
        print(f"CRASH: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
