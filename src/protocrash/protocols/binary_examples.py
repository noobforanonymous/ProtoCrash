"""
Example Binary Protocol Grammars
"""

from ..protocols.binary_grammar import (
    Grammar, UInt8, UInt16, UInt32, Bytes, String, Const, Endianness
)

# Simple custom protocol
CUSTOM_PROTOCOL = Grammar(
    "CustomProtocol",
    [
        Const("magic", b"\xDE\xAD\xBE\xEF"),
        UInt8("version"),
        UInt8("command"),
        UInt16("payload_length", Endianness.BIG),
        Bytes("payload", length_field="payload_length"),
        UInt32("checksum", Endianness.BIG)
    ]
)

# Network packet header
PACKET_HEADER = Grammar(
    "PacketHeader",
    [
        UInt32("magic", Endianness.BIG),
        UInt16("packet_type", Endianness.BIG),
        UInt32("sequence_number", Endianness.BIG),
        UInt16("data_length", Endianness.BIG),
        Bytes("data", length_field="data_length")
    ]
)

# TLV (Type-Length-Value)
TLV_MESSAGE = Grammar(
    "TLV",
    [
        UInt8("type"),
        UInt16("length", Endianness.BIG),
        Bytes("value", length_field="length")
    ]
)

# String-based protocol
STRING_PROTOCOL = Grammar(
    "StringProtocol",
    [
        UInt8("name_length"),
        String("name", length_field="name_length"),
        UInt16("data_length", Endianness.BIG),
        Bytes("data", length_field="data_length")
    ]
)
