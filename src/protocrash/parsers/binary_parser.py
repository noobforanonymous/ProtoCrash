"""
Binary Protocol Parser
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from ..protocols.binary_grammar import Grammar

@dataclass
class BinaryMessage:
    """Represents a parsed binary message"""
    grammar: Grammar
    fields: Dict[str, Any] = field(default_factory=dict)
    raw_data: Optional[bytes] = None

    def to_bytes(self) -> bytes:
        """Reconstruct to bytes with auto length fixing"""
        return self.grammar.build(self.fields)

class BinaryParser:
    """Parser for binary protocols using grammar DSL"""

    @staticmethod
    def parse(data: bytes, grammar: Grammar) -> BinaryMessage:
        """
        Parse binary data using grammar

        Args:
            data: Raw binary data
            grammar: Binary protocol grammar

        Returns:
            BinaryMessage with parsed fields
        """
        try:
            fields = grammar.parse(data)
            return BinaryMessage(
                grammar=grammar,
                fields=fields,
                raw_data=data
            )
        except Exception as e:
            # Return empty message on parse failure
            return BinaryMessage(
                grammar=grammar,
                fields={},
                raw_data=data
            )

    @staticmethod
    def reconstruct(msg: BinaryMessage) -> bytes:
        """
        Reconstruct binary message to bytes
        Length fields are automatically fixed

        Args:
            msg: BinaryMessage to reconstruct

        Returns:
            Raw binary data
        """
        return msg.to_bytes()
