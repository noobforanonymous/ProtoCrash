"""
Stack trace parsing and symbolization
"""
import re
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pathlib import Path
@dataclass
class StackFrame:
    """Represents a single stack frame"""
    frame_number: int
    address: str
    function: Optional[str] = None
    module: Optional[str] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    offset: Optional[str] = None
    def __str__(self) -> str:
        """Human-readable representation"""
        parts = [f"#{self.frame_number}"]
        if self.address:
            parts.append(f"0x{self.address}")
        if self.function:
            parts.append(f"in {self.function}")
        if self.source_file and self.line_number:
            parts.append(f"at {self.source_file}:{self.line_number}")
        elif self.module:
            parts.append(f"({self.module})")
        return " ".join(parts)
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'frame': self.frame_number,
            'address': self.address,
            'function': self.function,
            'module': self.module,
            'file': self.source_file,
            'line': self.line_number,
            'offset': self.offset
        }
@dataclass
class StackTrace:
    """Represents a complete stack trace"""
    frames: List[StackFrame] = field(default_factory=list)
    crash_address: Optional[str] = None
    crash_instruction: Optional[str] = None
    def __len__(self) -> int:
        return len(self.frames)
    def __iter__(self):
        return iter(self.frames)
    def __getitem__(self, index):
        return self.frames[index]
    def add_frame(self, frame: StackFrame):
        """Add a frame to the trace"""
        self.frames.append(frame)
    def get_top_frames(self, n: int = 5) -> List[StackFrame]:
        """Get top N frames"""
        return self.frames[:n]
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'frames': [f.to_dict() for f in self.frames],
            'crash_address': self.crash_address,
            'crash_instruction': self.crash_instruction,
            'depth': len(self.frames)
        }
    def __str__(self) -> str:
        """Human-readable representation"""
        lines = []
        if self.crash_address:
            lines.append(f"Crash at: {self.crash_address}")
        lines.extend(str(frame) for frame in self.frames)
        return "\n".join(lines)
class GDBTraceParser:
    """Parse GDB backtrace output"""
    # Pattern: #0  0x00007ffff7a9e000 in main () at test.c:10
    FRAME_PATTERN = re.compile(
        r'#(\d+)\s+'                          # Frame number
        r'(?:0x([0-9a-fA-F]+)\s+in\s+)?'     # Optional address
        r'([^\(]+)'                           # Function name
        r'(?:\s*\([^\)]*\))?'                 # Optional arguments
        r'(?:\s+at\s+([^:]+):(\d+))?'        # Optional file:line
    )
    @classmethod
    def parse(cls, backtrace: str) -> StackTrace:
        """
        Parse GDB backtrace output
        Args:
            backtrace: GDB bt output
        Returns:
            StackTrace object
        """
        trace = StackTrace()
        for line in backtrace.split('\n'):
            line = line.strip()
            if not line or not line.startswith('#'):
                continue
            match = cls.FRAME_PATTERN.match(line)
            if not match:
                continue
            frame_num = int(match.group(1))
            address = match.group(2) or ""
            function = match.group(3).strip()
            source_file = match.group(4)
            line_num = int(match.group(5)) if match.group(5) else None
            frame = StackFrame(
                frame_number=frame_num,
                address=address,
                function=function,
                source_file=source_file,
                line_number=line_num
            )
            trace.add_frame(frame)
        return trace
class ASANTraceParser:
    """Parse AddressSanitizer stack trace"""
    # Pattern: #0 0x7f8b2c in malloc test.c:15:5
    #         : #0 0x7f8b2c in malloc (/lib/libc.so.6+0x7f8b2c)
    FRAME_PATTERN = re.compile(
        r'#(\d+)\s+'
        r'0x([0-9a-fA-F]+)\s+'
        r'(?:in\s+)?(\S+)'
        r'(?:\s+(\S+):(\d+)(?::(\d+))?'  # file:line:col
        r'|\s*\(([^\)]+)\))?'  # OR (module+offset)
    )
    @classmethod
    def parse(cls, stderr: bytes) -> StackTrace:
        """
        Parse ASAN stack trace from stderr
        Args:
            stderr: Raw stderr containing ASAN output
        Returns:
            StackTrace object
        """
        trace = StackTrace()
        stderr_str = stderr.decode('utf-8', errors='ignore')
        # Extract crash address from ASAN summary
        crash_match = re.search(r'located at address (0x[0-9a-fA-F]+)', stderr_str)
        if crash_match:
            trace.crash_address = crash_match.group(1)
        in_trace = False
        for line in stderr_str.split('\n'):
            line = line.strip()
            # Start of stack trace
            if 'SUMMARY:' in line or '#0' in line:
                in_trace = True
            if not in_trace or not line.startswith('#'):
                continue
            match = cls.FRAME_PATTERN.match(line)
            if not match:
                continue
            frame_num = int(match.group(1))
            address = match.group(2)
            function = match.group(3).strip()
            module = match.group(4)
            source_file = match.group(5)
            line_num = int(match.group(6)) if match.group(6) else None
            frame = StackFrame(
                frame_number=frame_num,
                address=address,
                function=function,
                module=module,
                source_file=source_file,
                line_number=line_num
            )
            trace.add_frame(frame)
        return trace
class MSANTraceParser:
    """Parse MemorySanitizer stack trace"""
    # MSAN format is similar to ASAN
    @classmethod
    def parse(cls, stderr: bytes) -> StackTrace:
        """Parse MSAN trace (delegates to ASAN parser)"""
        return ASANTraceParser.parse(stderr)
class UBSANTraceParser:
    """Parse UndefinedBehaviorSanitizer stack trace"""
    # Pattern: test.c:15:5: runtime error: signed integer overflow
    ERROR_PATTERN = re.compile(r'([^:]+):(\d+):(\d+):\s+runtime error:\s+(.+)')
    @classmethod
    def parse(cls, stderr: bytes) -> StackTrace:
        """
        Parse UBSAN error from stderr
        Args:
            stderr: Raw stderr containing UBSAN output
        Returns:
            StackTrace object with single frame
        """
        trace = StackTrace()
        stderr_str = stderr.decode('utf-8', errors='ignore')
        for line in stderr_str.split('\n'):
            match = cls.ERROR_PATTERN.search(line)
            if match:
                source_file = match.group(1)
                line_num = int(match.group(2))
                error_msg = match.group(4)
                # Create synthetic frame
                frame = StackFrame(
                    frame_number=0,
                    address="",
                    function=f"UBSAN: {error_msg}",
                    source_file=source_file,
                    line_number=line_num
                )
                trace.add_frame(frame)
                break  # Only first error
        return trace
class Symbolizer:
    """Symbolize addresses using addr2line"""
    @staticmethod
    def symbolize(binary_path: str, address: str) -> Optional[StackFrame]:
        """
        Symbolize an address using addr2line
        Args:
            binary_path: Path to binary
            address: Hex address to symbolize
        Returns:
            StackFrame with symbolized information or None
        """
        if not Path(binary_path).exists():
            return None
        try:
            result = subprocess.run(
                ['addr2line', '-e', binary_path, '-f', '-C', address],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return None
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return None
            function = lines[0]
            location = lines[1]
            # Parse file:line
            if ':' in location:
                parts = location.rsplit(':', 1)
                source_file = parts[0]
                line_num = int(parts[1]) if parts[1].isdigit() else None
            else:
                source_file = location
                line_num = None
            return StackFrame(
                frame_number=0,
                address=address,
                function=function if function != '??' else None,
                source_file=source_file if source_file != '??' else None,
                line_number=line_num
            )
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError):
            return None
class TraceParser:
    """
    Unified trace parser that auto-detects format
    """
    @staticmethod
    def parse(data: bytes) -> StackTrace:
        """
        Auto-detect and parse stack trace
        Args:
            data: Raw trace data (stderr or backtrace output)
        Returns:
            Parsed StackTrace
        """
        data_str = data.decode('utf-8', errors='ignore') if isinstance(data, bytes) else data
        # Detect format
        if 'AddressSanitizer' in data_str or 'heap-use-after-free' in data_str:
            return ASANTraceParser.parse(data if isinstance(data, bytes) else data.encode())
        if 'MemorySanitizer' in data_str:
            return MSANTraceParser.parse(data if isinstance(data, bytes) else data.encode())
        if 'runtime error' in data_str:
            return UBSANTraceParser.parse(data if isinstance(data, bytes) else data.encode())
        # Default to GDB format
        return GDBTraceParser.parse(data_str)
