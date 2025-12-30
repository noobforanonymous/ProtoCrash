#!/usr/bin/env python3
"""
Sample Corpus Generator

Generates sample seed inputs for fuzzing different protocols.
"""

import os
import struct
import argparse
from pathlib import Path


def generate_http_corpus(output_dir: Path):
    """Generate HTTP seed corpus"""
    seeds = [
        # GET requests
        b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n",
        b"GET /index.html HTTP/1.1\r\nHost: test\r\n\r\n",
        b"GET /api/users HTTP/1.1\r\nHost: api.example.com\r\nAuthorization: Bearer token\r\n\r\n",
        
        # POST requests
        b"POST /login HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 29\r\n\r\n{\"user\":\"admin\",\"pass\":\"test\"}",
        b"POST /upload HTTP/1.1\r\nContent-Type: multipart/form-data\r\nContent-Length: 100\r\n\r\n--boundary\r\nContent-Disposition: form-data; name=\"file\"\r\n\r\ndata\r\n--boundary--",
        
        # Edge cases
        b"OPTIONS * HTTP/1.1\r\nHost: *\r\n\r\n",
        b"HEAD / HTTP/1.0\r\n\r\n",
    ]
    
    http_dir = output_dir / "http"
    http_dir.mkdir(exist_ok=True)
    
    for i, seed in enumerate(seeds):
        (http_dir / f"seed_{i:03d}.bin").write_bytes(seed)
    
    print(f"Generated {len(seeds)} HTTP seeds in {http_dir}")


def generate_dns_corpus(output_dir: Path):
    """Generate DNS seed corpus"""
    seeds = []
    
    # Simple A query for example.com
    query = struct.pack('!H', 0x1234)  # Transaction ID
    query += struct.pack('!H', 0x0100)  # Flags: standard query
    query += struct.pack('!H', 1)  # Questions
    query += struct.pack('!H', 0)  # Answers
    query += struct.pack('!H', 0)  # Authority
    query += struct.pack('!H', 0)  # Additional
    
    # example.com
    query += b'\x07example\x03com\x00'
    query += struct.pack('!H', 1)  # Type A
    query += struct.pack('!H', 1)  # Class IN
    seeds.append(query)
    
    # Query for test.local
    query2 = struct.pack('!HHHHHH', 0x5678, 0x0100, 1, 0, 0, 0)
    query2 += b'\x04test\x05local\x00'
    query2 += struct.pack('!HH', 1, 1)
    seeds.append(query2)
    
    # MX query
    query3 = struct.pack('!HHHHHH', 0xABCD, 0x0100, 1, 0, 0, 0)
    query3 += b'\x04mail\x07example\x03com\x00'
    query3 += struct.pack('!HH', 15, 1)  # Type MX
    seeds.append(query3)
    
    dns_dir = output_dir / "dns"
    dns_dir.mkdir(exist_ok=True)
    
    for i, seed in enumerate(seeds):
        (dns_dir / f"seed_{i:03d}.bin").write_bytes(seed)
    
    print(f"Generated {len(seeds)} DNS seeds in {dns_dir}")


def generate_binary_corpus(output_dir: Path):
    """Generate custom binary protocol seed corpus"""
    MAGIC = 0xDEADBEEF
    seeds = []
    
    # Command 0: Echo
    msg = struct.pack('<I', MAGIC)  # Magic
    msg += struct.pack('BB', 1, 0)  # Version 1, Command 0 (echo)
    msg += struct.pack('<H', 5)  # Length
    msg += b"Hello"
    seeds.append(msg)
    
    # Command 1: Info
    msg2 = struct.pack('<IBBH', MAGIC, 1, 1, 0)
    seeds.append(msg2)
    
    # Command with payload
    msg3 = struct.pack('<I', MAGIC)
    msg3 += struct.pack('BBH', 1, 0, 10)
    msg3 += b"A" * 10
    seeds.append(msg3)
    
    binary_dir = output_dir / "binary"
    binary_dir.mkdir(exist_ok=True)
    
    for i, seed in enumerate(seeds):
        (binary_dir / f"seed_{i:03d}.bin").write_bytes(seed)
    
    print(f"Generated {len(seeds)} binary protocol seeds in {binary_dir}")


def main():
    parser = argparse.ArgumentParser(description="Generate sample fuzzing corpus")
    parser.add_argument("--output", "-o", default="./corpus", help="Output directory")
    parser.add_argument("--protocol", "-p", choices=["http", "dns", "binary", "all"], 
                        default="all", help="Protocol to generate")
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating corpus in {output_dir}")
    print("=" * 50)
    
    if args.protocol in ["http", "all"]:
        generate_http_corpus(output_dir)
    
    if args.protocol in ["dns", "all"]:
        generate_dns_corpus(output_dir)
    
    if args.protocol in ["binary", "all"]:
        generate_binary_corpus(output_dir)
    
    print("=" * 50)
    print("Corpus generation complete!")


if __name__ == "__main__":
    main()
