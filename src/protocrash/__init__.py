"""ProtoCrash - Coverage-guided protocol fuzzer"""

__version__ = "0.1.0"
__author__ = "Security Researcher"
__license__ = "MIT"

from protocrash.core.types import CrashInfo, CrashType, ParsedMessage, ProtocolType

__all__ = [
    "CrashInfo",
    "CrashType",
    "ParsedMessage",
    "ProtocolType",
    "__version__",
]
