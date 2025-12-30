"""Core types and data structures for ProtoCrash"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class ProtocolType(Enum):
    """Supported protocol types"""
    HTTP = "http"
    DNS = "dns"
    SMTP = "smtp"
    BINARY = "binary"
    CUSTOM = "custom"


class CrashType(Enum):
    """Types of crashes"""
    SEGV = "Segmentation Fault"
    ABRT = "Abort"
    ILL = "Illegal Instruction"
    FPE = "Floating Point Exception"
    BUS = "Bus Error"
    HANG = "Timeout/Hang"
    ASAN = "AddressSanitizer"
    MSAN = "MemorySanitizer"
    UBSAN = "UndefinedBehaviorSanitizer"


@dataclass
class ParsedMessage:
    """Parsed protocol message structure"""
    protocol: ProtocolType
    fields: Dict[str, Any]
    raw_data: bytes
    valid: bool
    errors: List[str]


@dataclass
class CrashInfo:
    """Information about a crash"""
    crashed: bool
    crash_type: Optional[CrashType] = None
    signal_number: Optional[int] = None
    exit_code: int = 0
    stdout: bytes = b""
    stderr: bytes = b""
    stack_trace: Optional[str] = None
    exploitability: Optional[str] = None
    input_data: Optional[bytes] = None
