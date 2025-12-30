"""Test configuration and fixtures"""

import pytest
from pathlib import Path


@pytest.fixture
def sample_http_request():
    """Sample HTTP request for testing"""
    return b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"


@pytest.fixture
def sample_dns_query():
    """Sample DNS query for testing"""
    return b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'


@pytest.fixture
def temp_corpus(tmp_path):
    """Temporary corpus directory"""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    return corpus_dir


@pytest.fixture
def temp_crashes(tmp_path):
    """Temporary crashes directory"""
    crash_dir = tmp_path / "crashes"
    crash_dir.mkdir()
    return crash_dir
