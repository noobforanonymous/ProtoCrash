#!/usr/bin/env python3
"""
Custom Binary Protocol Target - For Fuzzing Demo

A deliberately vulnerable binary protocol parser.
Protocol format:
  - Magic: 4 bytes (0xDEADBEEF)
  - Version: 1 byte
  - Command: 1 byte
  - Length: 2 bytes (little-endian)
  - Payload: variable

SECURITY WARNING: This is intentionally vulnerable code.
DO NOT use in production. For testing only.
"""

import struct
import sys

MAGIC = 0xDEADBEEF

class ProtocolParser:
    """Custom binary protocol parser with intentional bugs"""
    
    def __init__(self):
        self.buffer = bytearray(256)  # Fixed size buffer
    
    def parse(self, data: bytes) -> dict:
        """Parse binary protocol message"""
        if len(data) < 8:
            raise ValueError("Message too short")
        
        # Parse header
        magic = struct.unpack('<I', data[0:4])[0]
        if magic != MAGIC:
            raise ValueError(f"Invalid magic: 0x{magic:08X}")
        
        version = data[4]
        command = data[5]
        length = struct.unpack('<H', data[6:8])[0]
        
        # BUG 1: Integer overflow on length
        if length > 0xFF00:
            length = (length * 2) & 0xFFFF  # Overflow
        
        # BUG 2: No bounds checking on payload
        payload = data[8:8 + length]
        
        # BUG 3: Buffer overflow when copying
        if length > 0:
            for i in range(length):
                if i < len(payload):
                    self.buffer[i] = payload[i]  # Potential overflow
        
        # BUG 4: Null terminator issue
        if b'\x00' in payload:
            idx = payload.index(b'\x00')
            payload = payload[:idx]
        
        return {
            'version': version,
            'command': command,
            'length': length,
            'payload': payload
        }
    
    def execute_command(self, msg: dict) -> bytes:
        """Execute command - contains bugs"""
        cmd = msg['command']
        
        # Command 0: Echo
        if cmd == 0:
            return msg['payload']
        
        # Command 1: Info
        elif cmd == 1:
            return b"CustomProtocol v1.0\n"
        
        # Command 2: Process (buggy)
        elif cmd == 2:
            # BUG 5: Use after free simulation
            data = msg['payload']
            del data
            return data  # Use after delete
        
        # Command 3: Crash
        elif cmd == 3:
            raise RuntimeError("Intentional crash")
        
        # Command 4: Memory corruption
        elif cmd == 4:
            arr = [0] * 10
            idx = msg['length'] % 256
            arr[idx] = 1  # IndexError
            return b"OK"
        
        else:
            return b"Unknown command\n"


def main():
    """Process binary protocol from file or stdin"""
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'rb') as f:
            data = f.read()
    else:
        data = sys.stdin.buffer.read()
    
    try:
        parser = ProtocolParser()
        msg = parser.parse(data)
        response = parser.execute_command(msg)
        sys.stdout.buffer.write(response)
    except Exception as e:
        print(f"CRASH: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
