"""Test core types and data structures"""

import pytest
from protocrash.core.types import CrashInfo, CrashType, ParsedMessage, ProtocolType


class TestProtocolType:
    """Test ProtocolType enum"""

    def test_protocol_types_exist(self):
        """Test that all protocol types are defined"""
        assert ProtocolType.HTTP.value == "http"
        assert ProtocolType.DNS.value == "dns"
        assert ProtocolType.SMTP.value == "smtp"
        assert ProtocolType.BINARY.value == "binary"
        assert ProtocolType.CUSTOM.value == "custom"

    def test_protocol_type_equality(self):
        """Test protocol type comparison"""
        assert ProtocolType.HTTP == ProtocolType.HTTP
        assert ProtocolType.HTTP != ProtocolType.DNS


class TestCrashType:
    """Test CrashType enum"""

    def test_crash_types_exist(self):
        """Test that all crash types are defined"""
        assert CrashType.SEGV.value == "Segmentation Fault"
        assert CrashType.ABRT.value == "Abort"
        assert CrashType.ASAN.value == "AddressSanitizer"

    def test_crash_type_string_representation(self):
        """Test crash type string values"""
        assert CrashType.SEGV.value == "Segmentation Fault"
        assert CrashType.HANG.value == "Timeout/Hang"


class TestParsedMessage:
    """Test ParsedMessage dataclass"""

    def test_create_valid_message(self):
        """Test creating a valid parsed message"""
        msg = ParsedMessage(
            protocol=ProtocolType.HTTP,
            fields={"method": "GET", "path": "/"},
            raw_data=b"GET / HTTP/1.1\r\n\r\n",
            valid=True,
            errors=[],
        )

        assert msg.protocol == ProtocolType.HTTP
        assert msg.fields["method"] == "GET"
        assert msg.valid is True
        assert len(msg.errors) == 0

    def test_create_invalid_message(self):
        """Test creating an invalid parsed message"""
        msg = ParsedMessage(
            protocol=ProtocolType.HTTP,
            fields={},
            raw_data=b"INVALID",
            valid=False,
            errors=["Parse error"],
        )

        assert msg.valid is False
        assert len(msg.errors) == 1
        assert msg.errors[0] == "Parse error"


class TestCrashInfo:
    """Test CrashInfo dataclass"""

    def test_create_no_crash(self):
        """Test creating crash info for non-crash"""
        crash = CrashInfo(crashed=False)

        assert crash.crashed is False
        assert crash.crash_type is None
        assert crash.signal_number is None

    def test_create_segfault_crash(self):
        """Test creating crash info for segmentation fault"""
        crash = CrashInfo(
            crashed=True,
            crash_type=CrashType.SEGV,
            signal_number=11,
            stderr=b"Segmentation fault",
            input_data=b"A" * 10000,
        )

        assert crash.crashed is True
        assert crash.crash_type == CrashType.SEGV
        assert crash.signal_number == 11
        assert b"Segmentation fault" in crash.stderr
        assert len(crash.input_data) == 10000

    def test_create_asan_crash(self):
        """Test creating crash info for ASan crash"""
        crash = CrashInfo(
            crashed=True,
            crash_type=CrashType.ASAN,
            stderr=b"AddressSanitizer: heap-use-after-free",
            stack_trace="#0 main test.c:10",
            exploitability="HIGH",
        )

        assert crash.crash_type == CrashType.ASAN
        assert b"heap-use-after-free" in crash.stderr
        assert crash.stack_trace is not None
        assert crash.exploitability == "HIGH"

    def test_crash_info_defaults(self):
        """Test CrashInfo default values"""
        crash = CrashInfo(crashed=True, crash_type=CrashType.ABRT)

        assert crash.exit_code == 0
        assert crash.stdout == b""
        assert crash.stderr == b""
        assert crash.stack_trace is None
        assert crash.exploitability is None
        assert crash.input_data is None
