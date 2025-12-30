"""Test dictionary mutations"""

import pytest
from protocrash.mutators.dictionary import DictionaryManager


class TestDictionaryManager:
    """Test DictionaryManager class"""

    @pytest.fixture
    def manager(self):
        return DictionaryManager()

    def test_init_loads_dictionaries(self, manager):
        """Test that dictionaries are loaded on init"""
        assert "http" in manager.dictionaries
        assert "dns" in manager.dictionaries
        assert "smtp" in manager.dictionaries
        assert "sql" in manager.dictionaries
        assert "command" in manager.dictionaries

    def test_http_dictionary_content(self, manager):
        """Test HTTP dictionary contains expected tokens"""
        http_dict = manager.dictionaries["http"]

        assert b"GET" in http_dict
        assert b"POST" in http_dict
        assert b"HTTP/1.1" in http_dict
        assert b"Host:" in http_dict

    def test_dns_dictionary_content(self, manager):
        """Test DNS dictionary contains expected tokens"""
        dns_dict = manager.dictionaries["dns"]

        assert b"\x00\x01" in dns_dict  # A record
        assert b"\xC0\x0C" in dns_dict  # Compression pointer

    def test_smtp_dictionary_content(self, manager):
        """Test SMTP dictionary contains expected tokens"""
        smtp_dict = manager.dictionaries["smtp"]

        assert b"HELO" in smtp_dict
        assert b"MAIL FROM:" in smtp_dict

    def test_sql_dictionary_content(self, manager):
        """Test SQL dictionary contains injection patterns"""
        sql_dict = manager.dictionaries["sql"]

        assert b"' OR '1'='1" in sql_dict
        assert b"'; DROP TABLE" in sql_dict

    def test_command_dictionary_content(self, manager):
        """Test command injection dictionary"""
        command_dict = manager.dictionaries["command"]

        assert b"; ls" in command_dict
        assert b"`id`" in command_dict

    def test_inject_with_protocol(self, manager):
        """Test injecting token with specific protocol"""
        data = b"TEST"

        result = manager.inject(data, protocol="http")

        assert isinstance(result, bytes)
        assert len(result) > len(data)

    def test_inject_without_protocol(self, manager):
        """Test injecting token without protocol (uses all)"""
        data = b"TEST"

        result = manager.inject(data, protocol=None)

        assert isinstance(result, bytes)
        assert len(result) > len(data)

    def test_inject_empty_data(self, manager):
        """Test injection on empty data"""
        data = b""

        result = manager.inject(data)

        assert result == b""

    def test_replace_with_protocol(self, manager):
        """Test replacing range with specific protocol"""
        data = b"AAABBBCCC"

        result = manager.replace(data, start=3, end=6, protocol="http")

        assert isinstance(result, bytes)
        assert result[:3] == b"AAA"
        assert result[-3:] == b"CCC"

    def test_replace_without_protocol(self, manager):
        """Test replacing range without protocol"""
        data = b"AAABBBCCC"

        result = manager.replace(data, start=3, end=6, protocol=None)

        assert isinstance(result, bytes)

    def test_replace_full_range(self, manager):
        """Test replacing entire data"""
        data = b"REPLACE_ME"

        result = manager.replace(data, start=0, end=len(data), protocol="sql")

        assert isinstance(result, bytes)
        # Should be just a dictionary token
        assert len(result) > 0

    def test_inject_invalid_protocol(self, manager):
        """Test injection with non-existent protocol falls back to all"""
        data = b"TEST"

        result = manager.inject(data, protocol="nonexistent")

        # Should still work by using all dictionaries
        assert isinstance(result, bytes)
        assert len(result) > len(data)
