"""
HTTP Request Templates
"""

from typing import Dict, Optional
from ..parsers.http_parser import HttpRequest

class HttpTemplates:
    """Factory for common HTTP requests"""

    COMMON_HEADERS = {
        "User-Agent": ["ProtoCrash/1.0"],
        "Accept": ["*/*"],
        "Connection": ["keep-alive"]
    }

    @staticmethod
    def get(path: str = "/", headers: Optional[Dict[str, list]] = None) -> HttpRequest:
        """Create GET request"""
        req_headers = HttpTemplates.COMMON_HEADERS.copy()
        if headers:
            req_headers.update(headers)

        return HttpRequest(
            method="GET",
            path=path,
            headers=req_headers
        )

    @staticmethod
    def post(path: str = "/", body: bytes = b"", headers: Optional[Dict[str, list]] = None) -> HttpRequest:
        """Create POST request"""
        req_headers = HttpTemplates.COMMON_HEADERS.copy()
        req_headers["Content-Length"] = [str(len(body))]
        req_headers["Content-Type"] = ["application/x-www-form-urlencoded"]

        if headers:
            req_headers.update(headers)

        return HttpRequest(
            method="POST",
            path=path,
            headers=req_headers,
            body=body
        )

    @staticmethod
    def put(path: str = "/", body: bytes = b"", headers: Optional[Dict[str, list]] = None) -> HttpRequest:
        """Create PUT request"""
        req_headers = HttpTemplates.COMMON_HEADERS.copy()
        req_headers["Content-Length"] = [str(len(body))]

        if headers:
            req_headers.update(headers)

        return HttpRequest(
            method="PUT",
            path=path,
            headers=req_headers,
            body=body
        )

    @staticmethod
    def delete(path: str = "/", headers: Optional[Dict[str, list]] = None) -> HttpRequest:
        """Create DELETE request"""
        req_headers = HttpTemplates.COMMON_HEADERS.copy()
        if headers:
            req_headers.update(headers)

        return HttpRequest(
            method="DELETE",
            path=path,
            headers=req_headers
        )

    @staticmethod
    def with_auth(method: str = "GET", path: str = "/", token: str = "bearer_token") -> HttpRequest:
        """Create request with Bearer authentication"""
        headers = HttpTemplates.COMMON_HEADERS.copy()
        headers["Authorization"] = [f"Bearer {token}"]

        return HttpRequest(
            method=method,
            path=path,
            headers=headers
        )

    @staticmethod
    def with_cookie(method: str = "GET", path: str = "/", cookie: str = "session=abc123") -> HttpRequest:
        """Create request with cookie"""
        headers = HttpTemplates.COMMON_HEADERS.copy()
        headers["Cookie"] = [cookie]

        return HttpRequest(
            method=method,
            path=path,
            headers=headers
        )
