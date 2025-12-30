"""Sample integration test"""

import pytest


class TestBasicIntegration:
    """Basic integration tests"""

    def test_package_imports(self):
        """Test that package can be imported"""
        import sys
        if 'protocrash' in sys.modules:
            del sys.modules['protocrash']
            
        import protocrash
        assert protocrash.__version__ == "0.1.0"

    def test_core_types_imports(self):
        """Test importing core types"""
        from protocrash.core.types import CrashInfo, CrashType, ParsedMessage, ProtocolType

        # Verify types are accessible
        assert CrashType is not None
        assert ProtocolType is not None
        assert CrashInfo is not None
        assert ParsedMessage is not None

    def test_fixtures_available(self, sample_http_request, temp_corpus):
        """Test that pytest fixtures work"""
        assert sample_http_request.startswith(b"GET")
        assert temp_corpus.exists()
        assert temp_corpus.is_dir()
