"""
HTTP Protocol Mutator - Advanced
"""
import random
import string
from ..parsers.http_parser import HttpParser, HttpRequest
from ..protocols.http_payloads import HttpPayloads
class HttpMutator:
    """Advanced structure-aware HTTP mutator"""
    def __init__(self):
        self.parser = HttpParser()
        self.payloads = HttpPayloads()
    def mutate(self, data: bytes) -> bytes:
        """Parse, mutate structure, and reconstruct"""
        req = self.parser.parse(data)
        if not req:
            # Fallback to random bit flip if not valid HTTP
            return self._fallback_mutate(data)
        mutation_type = random.choice([
            "method", "path", "header_val", "header_key", "body",
            "cookie", "smuggling", "crlf_injection", "chunked"
        ])
        if mutation_type == "method":
            req.method = self._mutate_method(req.method)
        elif mutation_type == "path":
            req.path = self._mutate_path(req.path)
        elif mutation_type == "header_val":
            self._mutate_header_value(req)
        elif mutation_type == "header_key":
            self._mutate_header_key(req)
        elif mutation_type == "body":
            req.body = self._mutate_body(req.body)
        elif mutation_type == "cookie":
            self._mutate_cookie(req)
        elif mutation_type == "smuggling":
            return self._create_smuggling_request()
        elif mutation_type == "crlf_injection":
            self._inject_crlf(req)
        elif mutation_type == "chunked":
            self._mutate_chunked_encoding(req)
        return self.parser.reconstruct(req)
    def _fallback_mutate(self, data: bytes) -> bytes:
        """Simple bit flip fallback"""
        if not data:
            return data
        res = bytearray(data)
        pos = random.randint(0, len(res) - 1)
        res[pos] ^= random.randint(1, 255)
        return bytes(res)
    def _mutate_method(self, current: str) -> str:
        """Mutate HTTP method"""
        methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "TRACE",
                   "CONNECT", "PATCH", "PROPFIND", "PROPPATCH", "MKCOL", "COPY", "MOVE"]
        # Filter out current to ensure change
        candidates = [m for m in methods if m != current]
        if random.random() < 0.7 and candidates:
            return random.choice(candidates)
        else:
            # Generate invalid method
            return "".join(random.choices(string.ascii_uppercase, k=random.randint(10, 50)))
    def _mutate_path(self, current: str) -> str:
        """Mutate URL path using payload library"""
        return random.choice(self.payloads.PATH_PAYLOADS)
    def _mutate_header_value(self, req: HttpRequest) -> None:
        """Mutate a random header value with attack payloads"""
        if not req.headers:
            return
        key = random.choice(list(req.headers.keys()))
        attack_type = random.choice(list(self.payloads.HEADER_ATTACKS.keys()))
        payload = self.payloads.HEADER_ATTACKS[attack_type]
        # Replace the first value
        req.headers[key][0] = payload
    def _mutate_header_key(self, req: HttpRequest) -> None:
        """Inject a new header or duplicate existing"""
        if random.random() < 0.5:
            # Add random fuzz header
            header_name = random.choice(self.payloads.FUZZ_HEADERS)
            if header_name not in req.headers:
                req.headers[header_name] = []
            req.headers[header_name].append("fuzzed_value_" + str(random.randint(1, 1000)))
        else:
            # Duplicate an existing header
            if req.headers:
                existing_key = random.choice(list(req.headers.keys()))
                req.headers[existing_key].append("duplicate_" + str(random.randint(1, 100)))
    def _mutate_body(self, body: bytes) -> bytes:
        """Mutate body with various techniques"""
        if not body:
            return b"A" * random.randint(100, 1000)
        technique = random.choice(["append", "prepend", "replace", "truncate"])
        if technique == "append":
            return body + b"A" * random.randint(100, 1000)
        elif technique == "prepend":
            return b"B" * random.randint(100, 1000) + body
        elif technique == "replace":
            return b"X" * len(body)
        else:  # truncate
            if len(body) > 10:
                return body[:len(body)//2]
            return body
    def _mutate_cookie(self, req: HttpRequest) -> None:
        """Fuzz cookies with attack payloads"""
        payload = random.choice(self.payloads.COOKIE_PAYLOADS)
        if "Cookie" not in req.headers:
            req.headers["Cookie"] = []
        req.headers["Cookie"].append(payload)
    def _create_smuggling_request(self) -> bytes:
        """Generate HTTP request smuggling payload"""
        smuggling_type = random.choice(list(self.payloads.SMUGGLING_PAYLOADS.keys()))
        template = self.payloads.SMUGGLING_PAYLOADS[smuggling_type]
        req = HttpRequest(
            method="POST",
            path="/",
            headers=template["headers"],
            body=template["body"]
        )
        return self.parser.reconstruct(req)
    def _inject_crlf(self, req: HttpRequest) -> None:
        """Inject CRLF into headers for header splitting attacks"""
        if not req.headers:
            req.headers["X-Fuzz"] = []
        # Pick a random header
        header_name = random.choice(list(req.headers.keys()))
        # CRLF injection payloads
        crlf_payloads = [
            "test\r\nX-Injected: true",
            "test\r\n\r\nHTTP/1.1 200 OK",
            "test\r\nSet-Cookie: admin=true",
            "test\r\nContent-Length: 0\r\n\r\nHTTP/1.1 200 OK",
        ]
        # Ensure header has at least one value
        if not req.headers[header_name]:
            req.headers[header_name].append(random.choice(crlf_payloads))
        else:
            req.headers[header_name][0] = random.choice(crlf_payloads)
    def _mutate_chunked_encoding(self, req: HttpRequest) -> None:
        """Mutate chunked transfer encoding"""
        req.is_chunked = True
        # Add malformed chunked encoding
        if "Transfer-Encoding" not in req.headers:
            req.headers["Transfer-Encoding"] = []
        # Obfuscation techniques
        encodings = [
            "chunked",
            "chunked ",  # trailing space
            " chunked",  # leading space
            "chunked\t",  # tab
            "identity, chunked",
            "chunked, identity",
        ]
        # Clear and add new value
        req.headers["Transfer-Encoding"] = [random.choice(encodings)]
        # Also add Content-Length for CL.TE smuggling
        if random.random() < 0.5:
            req.headers["Content-Length"] = [str(random.randint(1, 100))]
