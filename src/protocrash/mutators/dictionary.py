"""Dictionary-based mutations"""

import random
from typing import Dict, List


class DictionaryManager:
    """Manage mutation dictionaries for protocol-aware fuzzing"""

    def __init__(self):
        self.dictionaries: Dict[str, List[bytes]] = {
            "http": self._load_http_dict(),
            "dns": self._load_dns_dict(),
            "smtp": self._load_smtp_dict(),
            "sql": self._load_sql_dict(),
            "command": self._load_command_dict(),
        }

    def inject(self, data: bytes, protocol: str = None) -> bytes:
        """
        Inject dictionary token into data

        Args:
            data: Input data
            protocol: Protocol name (http, dns, smtp, etc.)

        Returns:
            Data with injected token
        """
        if protocol and protocol in self.dictionaries:
            dict_words = self.dictionaries[protocol]
        else:
            # Use all dictionaries
            dict_words = []
            for words in self.dictionaries.values():
                dict_words.extend(words)

        if not dict_words or len(data) == 0:
            return data

        token = random.choice(dict_words)
        position = random.randint(0, len(data))

        return data[:position] + token + data[position:]

    def replace(self, data: bytes, start: int, end: int, protocol: str = None) -> bytes:
        """
        Replace range with dictionary token

        Args:
            data: Input data
            start: Start position
            end: End position
            protocol: Protocol name

        Returns:
            Data with replaced range
        """
        if protocol and protocol in self.dictionaries:
            dict_words = self.dictionaries[protocol]
        else:
            dict_words = []
            for words in self.dictionaries.values():
                dict_words.extend(words)

        if not dict_words:
            return data

        token = random.choice(dict_words)
        return data[:start] + token + data[end:]

    def _load_http_dict(self) -> List[bytes]:
        """Load HTTP protocol dictionary"""
        return [
            b"GET",
            b"POST",
            b"PUT",
            b"DELETE",
            b"HEAD",
            b"OPTIONS",
            b"PATCH",
            b"TRACE",
            b"CONNECT",
            b"HTTP/1.0",
            b"HTTP/1.1",
            b"HTTP/2.0",
            b"Host:",
            b"Content-Length:",
            b"Content-Type:",
            b"Transfer-Encoding:",
            b"chunked",
            b"Authorization:",
            b"Cookie:",
            b"Set-Cookie:",
            b"Accept:",
            b"User-Agent:",
            b"Referer:",
            b"Accept-Encoding:",
            b"Connection:",
            b"close",
            b"keep-alive",
            b"\r\n",
            b"\r\n\r\n",
            b"application/json",
            b"text/html",
            b"../",
            b"%00",
            b"?",
            b"&",
            b"=",
        ]

    def _load_dns_dict(self) -> List[bytes]:
        """Load DNS protocol dictionary"""
        return [
            b"\x00\x01",  # A record
            b"\x00\x02",  # NS record
            b"\x00\x05",  # CNAME
            b"\x00\x0F",  # MX
            b"\x00\x10",  # TXT
            b"\x00\x1C",  # AAAA
            b"\x00\xFF",  # ANY
            b"\xC0\x0C",  # Compression pointer
            b"\xC0\x00",  # Compression pointer to start
            b".com",
            b".org",
            b".net",
            b"localhost",
            b"example",
        ]

    def _load_smtp_dict(self) -> List[bytes]:
        """Load SMTP protocol dictionary"""
        return [
            b"HELO",
            b"EHLO",
            b"MAIL FROM:",
            b"RCPT TO:",
            b"DATA",
            b"QUIT",
            b"RSET",
            b"NOOP",
            b"HELP",
            b"VRFY",
            b"EXPN",
            b"\r\n",
            b"\r\n.\r\n",
            b"@",
            b"<",
            b">",
        ]

    def _load_sql_dict(self) -> List[bytes]:
        """Load SQL injection dictionary"""
        return [
            b"' OR '1'='1",
            b"'; DROP TABLE",
            b"' UNION SELECT",
            b"/*",
            b"*/",
            b"--",
            b"#",
            b"'",
            b'"',
            b"\\",
            b"%00",
            b"admin'--",
        ]

    def _load_command_dict(self) -> List[bytes]:
        """Load command injection dictionary"""
        return [
            b"; ls",
            b"| whoami",
            b"`id`",
            b"$(cat /etc/passwd)",
            b"&& curl",
            b"|| wget",
            b"; nc",
            b"`uname -a`",
            b"${IFS}",
            b"%0a",
        ]
