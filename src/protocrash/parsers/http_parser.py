"""
HTTP Protocol Parser
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from urllib.parse import urlparse, parse_qs

@dataclass
class HttpRequest:
    """Represents an HTTP Request"""
    method: str
    path: str
    version: str = "HTTP/1.1"
    headers: Dict[str, List[str]] = field(default_factory=dict)  # Support duplicate headers
    body: bytes = b""
    query_params: Dict[str, List[str]] = field(default_factory=dict)
    is_chunked: bool = False

    def to_bytes(self) -> bytes:
        """Convert back to bytes"""
        lines = [f"{self.method} {self.path} {self.version}"]

        # Handle duplicate headers
        for k, values in self.headers.items():
            for v in values:
                lines.append(f"{k}: {v}")

        # Empty line before body
        lines.append("")

        # Join with CRLF
        head = "\r\n".join(lines).encode('utf-8')

        # Handle chunked encoding
        if self.is_chunked:
            return head + b"\r\n" + self._encode_chunked(self.body)

        return head + b"\r\n" + self.body

    def _encode_chunked(self, data: bytes) -> bytes:
        """Encode data as chunked transfer encoding"""
        if not data:
            return b"0\r\n\r\n"

        hex_size = hex(len(data))[2:].encode('utf-8')
        return hex_size + b"\r\n" + data + b"\r\n0\r\n\r\n"

class HttpParser:
    """Custom lightweight HTTP parser"""

    @staticmethod
    def parse(data: bytes) -> Optional[HttpRequest]:
        """
        Parse raw bytes into HttpRequest
        Returns None if parsing fails completely (not HTTP-like)
        """
        try:
            # Split into header and body
            parts = data.split(b"\r\n\r\n", 1)
            header_part = parts[0].decode('utf-8', errors='ignore')
            body = parts[1] if len(parts) > 1 else b""

            lines = header_part.split('\r\n')
            if not lines:
                return None

            # Parse request line
            req_line = lines[0].split(' ')
            if len(req_line) < 2:
                return None

            method = req_line[0]
            path = req_line[1]
            version = req_line[2] if len(req_line) > 2 else "HTTP/1.1"

            # Parse query parameters
            query_params = {}
            if '?' in path:
                parsed = urlparse(path)
                query_params = parse_qs(parsed.query)

            # Parse headers (support duplicates)
            headers = {}
            for line in lines[1:]:
                if ':' in line:
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()

                    if key not in headers:
                        headers[key] = []
                    headers[key].append(val)

            # Check if chunked encoding
            is_chunked = False
            if "Transfer-Encoding" in headers:
                te = headers["Transfer-Encoding"][0].lower()
                if "chunked" in te:
                    is_chunked = True
                    body = HttpParser._decode_chunked(body)

            return HttpRequest(
                method=method,
                path=path,
                version=version,
                headers=headers,
                body=body,
                query_params=query_params,
                is_chunked=is_chunked
            )

        except Exception:
            return None

    @staticmethod
    def _decode_chunked(data: bytes) -> bytes:
        """Decode chunked transfer encoding"""
        try:
            result = bytearray()
            offset = 0

            while offset < len(data):
                # Find chunk size line
                newline_pos = data.find(b"\r\n", offset)
                if newline_pos == -1:
                    break

                chunk_size_str = data[offset:newline_pos].decode('utf-8', errors='ignore')
                chunk_size = int(chunk_size_str.strip(), 16)

                if chunk_size == 0:
                    break

                # Read chunk data
                chunk_start = newline_pos + 2
                chunk_end = chunk_start + chunk_size
                result.extend(data[chunk_start:chunk_end])

                # Move past chunk and trailing CRLF
                offset = chunk_end + 2

            return bytes(result)
        except:
            return data  # Return original if decode fails

    @staticmethod
    def reconstruct(req: HttpRequest) -> bytes:
        """Reconstruct bytes from HttpRequest object"""
        return req.to_bytes()
