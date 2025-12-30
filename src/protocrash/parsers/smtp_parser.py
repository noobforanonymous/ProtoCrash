"""
SMTP Protocol Parser (RFC 5321)
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional
from ..core.protocol_parser import ProtocolParser, ProtocolMessage
from ..core.protocol_registry import ProtocolRegistry
# SMTP Commands
class SMTPCommand:
    """SMTP command constants (RFC 5321)"""
    HELO = "HELO"
    EHLO = "EHLO"
    MAIL = "MAIL"
    RCPT = "RCPT"
    DATA = "DATA"
    RSET = "RSET"
    VRFY = "VRFY"
    EXPN = "EXPN"
    HELP = "HELP"
    NOOP = "NOOP"
    QUIT = "QUIT"
@dataclass
class SMTPCommandLine:
    """SMTP command from client"""
    verb: str
    argument: str = ""
    def __str__(self) -> str:
        if self.argument:
            return f"{self.verb} {self.argument}"
        return self.verb
@dataclass
class SMTPResponse:
    """SMTP response from server"""
    code: int
    message: str
    is_multiline: bool = False
    def __str__(self) -> str:
        return f"{self.code} {self.message}"
@dataclass
class SMTPMessage(ProtocolMessage):
    """SMTP session message"""
    commands: List[SMTPCommandLine] = field(default_factory=list)
    responses: List[SMTPResponse] = field(default_factory=list)
    data_content: Optional[bytes] = None  # Email body after DATA command
    @property
    def is_client_message(self) -> bool:
        """True if this is a client message (has commands)"""
        return len(self.commands) > 0
    @property
    def is_server_message(self) -> bool:
        """True if this is a server message (has responses)"""
        return len(self.responses) > 0
@ProtocolRegistry.register("smtp")
class SMTPParser(ProtocolParser):
    """SMTP protocol parser"""
    # SMTP command pattern: VERB [arguments]
    COMMAND_PATTERN = re.compile(rb'^([A-Z]{4})\s*(.*?)$', re.IGNORECASE)
    # SMTP response pattern: 3-digit code [message]
    RESPONSE_PATTERN = re.compile(rb'^(\d{3})([ -])(.*?)$')
    @property
    def protocol_name(self) -> str:
        return "smtp"
    def parse(self, data: bytes) -> Optional[SMTPMessage]:
        """
        Parse SMTP message (commands or responses)
        Args:
            data: Raw SMTP data
        Returns:
            SMTPMessage or None if invalid
        """
        try:
            lines = data.split(b'\r\n')
            msg = SMTPMessage(raw_data=data)
            # Detect if this is a command or response
            if lines and lines[0]:
                # Try parsing as response first (starts with 3 digits)
                if self.RESPONSE_PATTERN.match(lines[0]):
                    return self._parse_responses(lines, msg)
                # Otherwise parse as commands
                else:
                    return self._parse_commands(lines, msg)
            return msg
        except Exception:
            return None
    def _parse_commands(self, lines: List[bytes], msg: SMTPMessage) -> SMTPMessage:
        """Parse SMTP commands from client"""
        in_data_mode = False
        data_lines = []
        for line in lines:
            if not line:
                continue
            # Check for end of DATA
            if in_data_mode:
                if line == b'.':
                    msg.data_content = b'\r\n'.join(data_lines)
                    in_data_mode = False
                else:
                    data_lines.append(line)
                continue
            # Parse command
            match = self.COMMAND_PATTERN.match(line)
            if match:
                verb = match.group(1).decode('utf-8', errors='ignore').upper()
                arg = match.group(2).decode('utf-8', errors='ignore').strip()
                msg.commands.append(SMTPCommandLine(verb, arg))
                # Enter DATA mode after DATA command
                if verb == "DATA":
                    in_data_mode = True
            else:
                # Could be continuation of previous command or malformed
                # Try to parse as simple text
                text = line.decode('utf-8', errors='ignore').strip()
                if text:
                    # Check if it's a known command without pattern match
                    parts = text.split(None, 1)
                    if parts:
                        verb = parts[0].upper()
                        arg = parts[1] if len(parts) > 1 else ""
                        msg.commands.append(SMTPCommandLine(verb, arg))
        return msg
    def _parse_responses(self, lines: List[bytes], msg: SMTPMessage) -> SMTPMessage:
        """Parse SMTP responses from server"""
        current_response = None
        response_lines = []
        for line in lines:
            if not line:
                continue
            match = self.RESPONSE_PATTERN.match(line)
            if match:
                code = int(match.group(1))
                separator = match.group(2).decode('utf-8')
                message = match.group(3).decode('utf-8', errors='ignore')
                # Check if multiline (separator is '-')
                if separator == '-':
                    if current_response is None:
                        current_response = SMTPResponse(code, message, True)
                        response_lines = [message]
                    else:
                        response_lines.append(message)
                else:
                    # End of response
                    if current_response:
                        # Finish multiline response
                        response_lines.append(message)
                        current_response.message = '\n'.join(response_lines)
                        msg.responses.append(current_response)
                        current_response = None
                        response_lines = []
                    else:
                        # Single line response
                        msg.responses.append(SMTPResponse(code, message, False))
        # Add any remaining multiline response
        if current_response:
            current_response.message = '\n'.join(response_lines)
            msg.responses.append(current_response)
        return msg
    def reconstruct(self, message: SMTPMessage) -> bytes:
        """
        Reconstruct SMTP message to bytes
        Args:
            message: SMTPMessage object
        Returns:
            Raw SMTP data
        """
        result = bytearray()
        # Build commands
        for cmd in message.commands:
            line = f"{cmd.verb}"
            if cmd.argument:
                line += f" {cmd.argument}"
            result.extend(line.encode('utf-8'))
            result.extend(b'\r\n')
            # Add DATA content after DATA command
            if cmd.verb == "DATA" and message.data_content:
                result.extend(message.data_content)
                result.extend(b'\r\n.\r\n')
        # Build responses
        for resp in message.responses:
            if resp.is_multiline:
                lines = resp.message.split('\n')
                for i, line in enumerate(lines):
                    separator = '-' if i < len(lines) - 1 else ' '
                    result.extend(f"{resp.code}{separator}{line}\r\n".encode('utf-8'))
            else:
                result.extend(f"{resp.code} {resp.message}\r\n".encode('utf-8'))
        return bytes(result)
    def detect(self, data: bytes, port: Optional[int] = None) -> float:
        """
        Detect if data is SMTP protocol
        Args:
            data: Raw data
            port: Optional port hint
        Returns:
            Confidence 0.0-1.0
        """
        confidence = 0.0
        # Port hint
        if port in (25, 587, 465, 2525):
            confidence += 0.3
        if len(data) < 4:
            return 0.0
        try:
            # Try to decode as text
            text = data.decode('utf-8', errors='ignore')
            lines = text.split('\r\n')
            if not lines:
                return 0.0
            first_line = lines[0].strip()
            if not first_line:
                return 0.0
            # Check for SMTP response code (3 digits)
            if self.RESPONSE_PATTERN.match(first_line.encode()):
                code_str = first_line[:3]
                if code_str.isdigit():
                    code = int(code_str)
                    # Valid SMTP response codes
                    if 200 <= code < 600:
                        confidence += 0.5
                        # Check for common greeting codes
                        if code in (220, 250, 354, 421, 450, 451, 500, 501, 550):
                            confidence += 0.2
            # Check for SMTP commands
            elif self.COMMAND_PATTERN.match(first_line.encode()):
                verb = first_line.split()[0].upper() if first_line.split() else ""
                smtp_commands = {'HELO', 'EHLO', 'MAIL', 'RCPT', 'DATA', 'QUIT', 'RSET', 'NOOP', 'VRFY'}
                if verb in smtp_commands:
                    confidence += 0.6
                    # MAIL FROM or RCPT TO patterns
                    if 'FROM:' in first_line.upper() or 'TO:' in first_line.upper():
                        confidence += 0.2
        except Exception:
            return 0.0
        return min(1.0, confidence)
