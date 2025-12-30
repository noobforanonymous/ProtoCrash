"""
SMTP-specific mutation strategies
"""
import random
from ..parsers.smtp_parser import SMTPParser, SMTPMessage, SMTPCommandLine, SMTPResponse
class SMTPMutator:
    """SMTP protocol-specific mutator"""
    def __init__(self):
        self.parser = SMTPParser()
        # Interesting SMTP values
        self.interesting_codes = [
            200, 211, 214, 220, 221, 250, 251, 252,  # 2xx success
            354,  # 3xx intermediate
            421, 450, 451, 452,  # 4xx temporary failure
            500, 501, 502, 503, 504, 550, 551, 552, 553, 554,  # 5xx permanent failure
            0, 99, 199, 600, 999  # Invalid codes
        ]
        self.smtp_commands = [
            'HELO', 'EHLO', 'MAIL', 'RCPT', 'DATA', 'RSET',
            'VRFY', 'EXPN', 'HELP', 'NOOP', 'QUIT',
            'AUTH', 'STARTTLS'  # Extensions
        ]
    def mutate(self, data: bytes) -> bytes:
        """
        Main mutation entry point
        Args:
            data: SMTP message bytes
        Returns:
            Mutated SMTP message
        """
        #Try to parse as SMTP
        msg = self.parser.parse(data)
        if not msg:
            # Not valid SMTP, return basic mutation
            return self._mutate_raw(data)
        # Select random mutation strategy
        strategies = [
            self.mutate_commands,
            self.mutate_responses,
            self.mutate_data_content,
            self.mutate_line_lengths,
            self.mutate_crlf,
        ]
        strategy = random.choice(strategies)
        mutated_msg = strategy(msg)
        return self.parser.reconstruct(mutated_msg)
    def mutate_commands(self, msg: SMTPMessage) -> SMTPMessage:
        """Mutate SMTP commands"""
        if not msg.commands:
            # Add a random command
            msg.commands.append(
                SMTPCommandLine(random.choice(self.smtp_commands), 'test.com')
            )
            return msg
        cmd = random.choice(msg.commands)
        mutation_type = random.choice(['verb', 'argument', 'case', 'invalid'])
        if mutation_type == 'verb':
            # Change command verb
            cmd.verb = random.choice(self.smtp_commands + ['INVALID', 'XXX', 'TEST', ''])
        elif mutation_type == 'argument':
            # Mutate argument
            cmd.argument = self._mutate_smtp_argument(cmd.verb, cmd.argument)
        elif mutation_type == 'case':
            # Mix case (smtp is case-insensitive)
            cmd.verb = ''.join(
                c.upper() if random.random() < 0.5 else c.lower()
                for c in cmd.verb
            )
        else:  # invalid
            # Create completely invalid command
            cmd.verb = ''.join(chr(random.randint(33, 126)) for _ in range(random.randint(1, 20)))
            cmd.argument = ''.join(chr(random.randint(0, 127)) for _ in range(random.randint(0, 100)))
        return msg
    def mutate_responses(self, msg: SMTPMessage) -> SMTPMessage:
        """Mutate SMTP responses"""
        if not msg.responses:
            # Add a random response
            msg.responses.append(
                SMTPResponse(random.choice(self.interesting_codes), 'OK', False)
            )
            return msg
        resp = random.choice(msg.responses)
        mutation_type = random.choice(['code', 'message', 'multiline'])
        if mutation_type == 'code':
            # Change response code
            resp.code = random.choice(self.interesting_codes)
        elif mutation_type == 'message':
            # Mutate response message
            resp.message = self._mutate_response_message(resp.message)
        else:  # multiline
            # Toggle or corrupt multiline
            resp.is_multiline = not resp.is_multiline
            if resp.is_multiline:
                # Add multiple lines
                resp.message = resp.message + '\n' + 'Extra line\nAnother line'
        return msg
    def mutate_data_content(self, msg: SMTPMessage) -> SMTPMessage:
        """Mutate DATA content"""
        if msg.data_content is None:
            # Add random DATA content
            msg.data_content = b'Subject: Test\r\n\r\nBody'
            return msg
        mutation_type = random.choice(['headers', 'body', 'boundaries', 'size'])
        if mutation_type == 'headers':
            # Corrupt email headers
            content = msg.data_content.decode('utf-8', errors='ignore')
            headers = [
                'From: ' + self._random_email(),
                'To: ' + self._random_email(),
                'Subject: ' + self._random_string(50),
                'Date: ' + self._random_date(),
                'X-Invalid: ' + '\x00\x01\x02',  # Invalid chars
            ]
            new_headers = '\r\n'.join(random.sample(headers, random.randint(1, len(headers))))
            msg.data_content = (new_headers + '\r\n\r\n' + content.split('\r\n\r\n', 1)[-1]).encode()
        elif mutation_type == 'body':
            # Mutate email body
            content = bytearray(msg.data_content)
            for _ in range(min(10, len(content))):
                if content:
                    content[random.randint(0, len(content) - 1)] = random.randint(0, 255)
            msg.data_content = bytes(content)
        elif mutation_type == 'boundaries':
            # Add dot-stuffing issues or line endings
            content = msg.data_content.decode('utf-8', errors='ignore')
            # Add lines starting with dots (should be stuffed)
            content = content.replace('\r\n', '\r\n.' + 'test' * 10 + '\r\n')
            msg.data_content = content.encode()
        else:  # size
            # Make very large or very small
            if random.random() < 0.5:
                # Very large
                msg.data_content += b'X' * random.randint(10000, 100000)
            else:
                # Very small
                msg.data_content = b'X'
        return msg
    def mutate_line_lengths(self, msg: SMTPMessage) -> SMTPMessage:
        """Mutate to create line length violations (>998 chars per RFC)"""
        if msg.commands:
            cmd = random.choice(msg.commands)
            # Create very long argument
            cmd.argument = 'A' * random.randint(1000, 10000)
        if msg.responses:
            resp = random.choice(msg.responses)
            # Create very long message
            resp.message = 'B' * random.randint(1000, 10000)
        return msg
    def mutate_crlf(self, msg: SMTPMessage) -> SMTPMessage:
        """Mutate CRLF handling - ensure message has commands or responses"""
        # Ensure we have something to mutate
        if not msg.commands and not msg.responses:
            msg.commands.append(SMTPCommandLine('HELO', 'test.com'))
        return msg
    def _mutate_smtp_argument(self, verb: str, argument: str) -> str:
        """Mutate SMTP command argument based on verb"""
        if verb in ('MAIL', 'RCPT'):
            # Email address mutation
            if 'FROM' in argument.upper() or 'TO' in argument.upper():
                # Extract and mutate email
                email = self._random_email()
                prefix = 'FROM:' if 'FROM' in argument.upper() else 'TO:'
                return f'{prefix}<{email}>'
            return argument
        elif verb in ('HELO', 'EHLO'):
            # Domain mutation
            return self._random_domain()
        elif verb == 'VRFY':
            # Username mutation
            return self._random_string(random.randint(1, 50))
        else:
            # Generic mutation
            mutations = [
                '',  # Empty
                'A' * random.randint(500, 2000),  # Very long
                '\x00\x01\x02',  # Invalid chars
                self._random_string(100),
            ]
            return random.choice(mutations)
    def _mutate_response_message(self, message: str) -> str:
        """Mutate SMTP response message"""
        mutations = [
            '',  # Empty
            'A' * random.randint(500, 2000),  # Very long
            message + '\x00\x01\x02',  # Add invalid chars
            'OK ' * 100,  # Repetitive
            self._random_string(100),
        ]
        return random.choice(mutations)
    def _random_email(self) -> str:
        """Generate random email address"""
        mutations = [
            f'user{random.randint(1,1000)}@example.com',
            f'{"a"*100}@test.com',  # Long local part
            f'user@{"b"*100}.com',  # Long domain
            'invalid@',  # Missing domain
            '@invalid.com',  # Missing local
            'no-at-sign.com',  # Missing @
            'user@domain@extra.com',  # Multiple @
            '',  # Empty
        ]
        return random.choice(mutations)
    def _random_domain(self) -> str:
        """Generate random domain"""
        return f'{"test"*random.randint(1,20)}.{"com"*random.randint(1,10)}'
    def _random_string(self, length: int) -> str:
        """Generate random string"""
        return ''.join(chr(random.randint(33, 126)) for _ in range(length))
    def _random_date(self) -> str:
        """Generate random date string"""
        return f'{random.randint(1,31)} Jan {random.randint(1970,2030)} 12:00:00 +0000'
    def _mutate_raw(self, data: bytes) -> bytes:
        """Basic byte-level mutation for non-parseable data"""
        data = bytearray(data)
        mutation_type = random.choice(['flip', 'insert', 'delete', 'replace'])
        if mutation_type == 'flip' and data:
            # Flip random bytes
            for _ in range(min(5, len(data))):
                data[random.randint(0, len(data) - 1)] ^= 0xFF
        elif mutation_type == 'insert':
            # Insert random bytes
            pos = random.randint(0, len(data))
            data = data[:pos] + bytes(random.randint(0, 255) for _ in range(10)) + data[pos:]
        elif mutation_type == 'delete' and len(data) > 10:
            # Delete some bytes
            start = random.randint(0, len(data) - 10)
            data = data[:start] + data[start+10:]
        else:  # replace
            # Replace section with random data
            if len(data) > 5:
                start = random.randint(0, len(data) - 5)
                for i in range(start, min(start + 5, len(data))):
                    data[i] = random.randint(0, 255)
        return bytes(data)
