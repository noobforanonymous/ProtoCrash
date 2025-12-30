#!/usr/bin/env python3
"""
Simple HTTP Server Target - For Fuzzing Demo

A deliberately vulnerable HTTP server for testing ProtoCrash.
Contains intentional bugs for demonstration purposes.

SECURITY WARNING: This is intentionally vulnerable code.
DO NOT use in production. For testing only.
"""

import socket
import sys
import signal

def handle_request(data: bytes) -> bytes:
    """Handle HTTP request - contains intentional bugs"""
    try:
        request = data.decode('utf-8', errors='ignore')
        lines = request.split('\r\n')
        
        if not lines:
            return b"HTTP/1.1 400 Bad Request\r\n\r\n"
        
        # Parse request line
        parts = lines[0].split(' ')
        if len(parts) < 2:
            return b"HTTP/1.1 400 Bad Request\r\n\r\n"
        
        method, path = parts[0], parts[1]
        
        # BUG 1: Path traversal (intentional vulnerability)
        if '../' in path:
            # Simulate crash on path traversal
            raise ValueError("Path traversal detected")
        
        # BUG 2: Buffer overflow simulation
        if len(path) > 1000:
            # Simulate buffer overflow crash
            arr = [0] * 10
            arr[len(path)] = 1  # IndexError - simulates crash
        
        # BUG 3: Format string simulation
        if '%s%s%s' in path:
            # Simulate format string crash
            raise MemoryError("Format string attack")
        
        # BUG 4: Null byte injection
        if '\x00' in path:
            raise RuntimeError("Null byte injection")
        
        # Normal response
        response = f"""HTTP/1.1 200 OK\r
Content-Type: text/html\r
Content-Length: 13\r
\r
Hello World!
"""
        return response.encode()
        
    except Exception as e:
        # Crash on any exception (for fuzzing demo)
        print(f"CRASH: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Run HTTP server"""
    if len(sys.argv) > 1:
        # File input mode for fuzzing
        with open(sys.argv[1], 'rb') as f:
            data = f.read()
        response = handle_request(data)
        print(response.decode(), end='')
        return
    
    # Socket mode
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('127.0.0.1', 8080))
    sock.listen(5)
    
    print("HTTP Server listening on 127.0.0.1:8080")
    
    while True:
        conn, addr = sock.accept()
        data = conn.recv(4096)
        if data:
            response = handle_request(data)
            conn.sendall(response)
        conn.close()

if __name__ == '__main__':
    main()
