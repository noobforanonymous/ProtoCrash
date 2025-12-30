"""
Protocol Auto-Detection System
"""

from typing import Optional, Tuple
from .protocol_registry import ProtocolRegistry


class ProtocolDetector:
    """
    Intelligent protocol detection using multiple strategies
    """

    # Port-based hints
    PORT_HINTS = {
        53: "dns",
        25: "smtp",
        587: "smtp",
        465: "smtp",
        80: "http",
        443: "http",
        8080: "http",
    }

    def __init__(self, registry: Optional[ProtocolRegistry] = None):
        """
        Initialize detector

        Args:
            registry: Protocol registry (uses default if None)
        """
        self.registry = registry or ProtocolRegistry

    def detect(self, data: bytes, port: Optional[int] = None) -> Tuple[Optional[str], float]:
        """
        Detect protocol using port hints and signature analysis

        Args:
            data: Raw protocol data
            port: Optional port number

        Returns:
            (protocol_name, confidence)
        """
        # Strategy 1: Port-based hint
        if port and port in self.PORT_HINTS:
            suggested_protocol = self.PORT_HINTS[port]
            parser_class = self.registry.get_parser(suggested_protocol)

            if parser_class:
                parser = parser_class()
                confidence = parser.detect(data, port)

                # Boost confidence if port matches
                boosted_confidence = min(1.0, confidence * 1.2)

                if boosted_confidence >= 0.6:
                    return suggested_protocol, boosted_confidence

        # Strategy 2: Full auto-detection
        return self.registry.auto_detect(data, port)

    def detect_with_fallback(self, data: bytes, port: Optional[int] = None,
                            fallback: str = "binary") -> Tuple[str, float]:
        """
        Detect protocol with fallback to default

        Args:
            data: Raw protocol data
            port: Optional port number
            fallback: Default protocol if detection fails

        Returns:
            (protocol_name, confidence)
        """
        protocol, confidence = self.detect(data, port)

        if protocol:
            return protocol, confidence

        return fallback, 0.1  # Low confidence fallback
