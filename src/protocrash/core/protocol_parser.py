"""
Protocol Parser Abstract Base Class
Defines interface for all protocol parsers
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
@dataclass
class ProtocolMessage(ABC):
    """Base class for protocol-specific messages"""
    raw_data: Optional[bytes] = None
class ProtocolParser(ABC):
    """
    Abstract base class for all protocol parsers
    This interface enables:
    - Pluggable protocol support
    - Auto-detection
    - Consistent parsing/reconstruction API
    """
    @abstractmethod
    def parse(self, data: bytes) -> Optional[ProtocolMessage]:
        """
        Parse raw bytes into protocol message
        Args:
            data: Raw protocol data
        Returns:
            Parsed message or None if invalid
        """
        pass
    @abstractmethod
    def reconstruct(self, message: ProtocolMessage) -> bytes:
        """
        Reconstruct protocol message to bytes
        Args:
            message: Protocol message object
        Returns:
            Raw bytes representation
        """
        pass
    @abstractmethod
    def detect(self, data: bytes, port: Optional[int] = None) -> float:
        """
        Detect if data matches this protocol
        Args:
            data: Raw data to analyze
            port: Optional port number hint
        Returns:
            Confidence score 0.0 (not this protocol) to 1.0 (definitely this protocol)
        """
        pass
    @property
    @abstractmethod
    def protocol_name(self) -> str:
        """Return protocol name (e.g., 'http', 'dns', 'smtp')"""
        pass
