"""
Protocol Registry System
Manages protocol parser plugins and auto-detection
"""

from typing import Dict, Type, Optional, Tuple, List
from .protocol_parser import ProtocolParser


class ProtocolRegistry:
    """
    Central registry for protocol parsers

    Enables:
    - Dynamic parser registration
    - Protocol auto-detection
    - Parser retrieval by name
    """

    _parsers: Dict[str, Type[ProtocolParser]] = {}

    @classmethod
    def register(cls, name: str):
        """
        Decorator to register a protocol parser

        Usage:
            @ProtocolRegistry.register("http")
            class HttpParser(ProtocolParser):
                ...
        """
        def decorator(parser_class: Type[ProtocolParser]):
            cls._parsers[name.lower()] = parser_class
            return parser_class
        return decorator

    @classmethod
    def register_parser(cls, name: str, parser_class: Type[ProtocolParser]) -> None:
        """
        Manually register a protocol parser

        Args:
            name: Protocol name
            parser_class: Parser class implementing ProtocolParser
        """
        cls._parsers[name.lower()] = parser_class

    @classmethod
    def get_parser(cls, name: str) -> Optional[Type[ProtocolParser]]:
        """
        Get parser class by protocol name

        Args:
            name: Protocol name

        Returns:
            Parser class or None if not found
        """
        return cls._parsers.get(name.lower())

    @classmethod
    def list_protocols(cls) -> List[str]:
        """
        Get list of registered protocol names

        Returns:
            List of protocol names
        """
        return list(cls._parsers.keys())

    @classmethod
    def auto_detect(cls, data: bytes, port: Optional[int] = None) -> Tuple[Optional[str], float]:
        """
        Auto-detect protocol from data

        Args:
            data: Raw protocol data
            port: Optional port number hint

        Returns:
            (protocol_name, confidence) or (None, 0.0) if no match
        """
        best_match = None
        best_confidence = 0.0

        for name, parser_class in cls._parsers.items():
            parser = parser_class()
            confidence = parser.detect(data, port)

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = name

        # Only return if confidence is reasonable
        if best_confidence >= 0.5:
            return best_match, best_confidence

        return None, 0.0

    @classmethod
    def clear(cls) -> None:
        """Clear all registered parsers (mainly for testing)"""
        cls._parsers.clear()
