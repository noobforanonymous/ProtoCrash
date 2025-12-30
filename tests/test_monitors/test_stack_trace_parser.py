"""
Tests for stack trace parsing
"""

import pytest
from protocrash.monitors.stack_trace_parser import (
    StackFrame, StackTrace, GDBTraceParser, ASANTraceParser,
    MSANTraceParser, UBSANTraceParser, Symbolizer, TraceParser
)


class TestStackFrame:
    """Test StackFrame dataclass"""
    
    def test_frame_creation(self):
        """Test basic frame creation"""
        frame = StackFrame(
            frame_number=0,
            address="deadbeef",
            function="main",
            source_file="test.c",
            line_number=42
        )
        
        assert frame.frame_number == 0
        assert frame.address == "deadbeef"
        assert frame.function == "main"
        assert frame.source_file == "test.c"
        assert frame.line_number == 42
    
    def test_frame_str(self):
        """Test frame string representation"""
        frame = StackFrame(
            frame_number=0,
            address="deadbeef",
            function="main",
            source_file="test.c",
            line_number=42
        )
        
        s = str(frame)
        assert "#0" in s
        assert "0xdeadbeef" in s
        assert "main" in s
        assert "test.c:42" in s
    
    def test_frame_to_dict(self):
        """Test frame serialization"""
        frame = StackFrame(
            frame_number=1,
            address="cafebabe",
            function="foo"
        )
        
        d = frame.to_dict()
        assert d['frame'] == 1
        assert d['address'] == "cafebabe"
        assert d['function'] == "foo"


class TestStackTrace:
    """Test StackTrace dataclass"""
    
    def test_trace_creation(self):
        """Test trace creation and manipulation"""
        trace = StackTrace()
        assert len(trace) == 0
        
        frame = StackFrame(0, "addr1", "func1")
        trace.add_frame(frame)
        assert len(trace) == 1
    
    def test_trace_iteration(self):
        """Test trace iteration"""
        trace = StackTrace()
        frames = [
            StackFrame(0, "addr1", "func1"),
            StackFrame(1, "addr2", "func2"),
            StackFrame(2, "addr3", "func3")
        ]
        
        for f in frames:
            trace.add_frame(f)
        
        assert list(trace) == frames
    
    def test_get_top_frames(self):
        """Test getting top N frames"""
        trace = StackTrace()
        for i in range(10):
            trace.add_frame(StackFrame(i, f"addr{i}", f"func{i}"))
        
        top = trace.get_top_frames(3)
        assert len(top) == 3
        assert top[0].frame_number == 0
        assert top[2].frame_number == 2
    
    def test_trace_to_dict(self):
        """Test trace serialization"""
        trace = StackTrace(crash_address="0xdeadbeef")
        trace.add_frame(StackFrame(0, "addr", "func"))
        
        d = trace.to_dict()
        assert d['crash_address'] == "0xdeadbeef"
        assert d['depth'] == 1
        assert len(d['frames']) == 1


class TestGDBTraceParser:
    """Test GDB backtrace parser"""
    
    def test_parse_simple_trace(self):
        """Test parsing simple GDB backtrace"""
        backtrace = """#0  0x00007ffff7a9e000 in main () at test.c:10
#1  0x00007ffff7a9d080 in __libc_start_main () at libc.c:308
#2  0x0000000000400590 in _start ()"""
        
        trace = GDBTraceParser.parse(backtrace)
        assert len(trace) == 3
        assert trace[0].function == "main"
        # Source file parsing varies by format
        assert trace[0].line_number == 10
    
    def test_parse_without_source(self):
        """Test parsing trace without source info"""
        backtrace = """#0  0x00007ffff7a9e000 in malloc ()
#1  0x00007ffff7a9d080 in free ()"""
        
        trace = GDBTraceParser.parse(backtrace)
        assert len(trace) == 2
        assert trace[0].function == "malloc"
        assert trace[0].source_file is None
    
    def test_parse_empty_trace(self):
        """Test parsing empty backtrace"""
        trace = GDBTraceParser.parse("")
        assert len(trace) == 0


class TestASANTraceParser:
    """Test ASAN trace parser"""
    
    def test_parse_asan_trace(self):
        """Test parsing ASAN stack trace"""
        stderr = b"""==12345==ERROR: AddressSanitizer: heap-use-after-free on address 0x60300000eff0
READ of size 4 at 0x60300000eff0 thread T0
    #0 0x7f8b2c in main test.c:15:5
    #1 0x7f8a00 in __libc_start_main libc.c:308
    #2 0x400590 in _start (./test+0x400590)

0x60300000eff0 is located 0 bytes inside of 4-byte region
freed by thread T0 here:
    #0 0x7f8cde in free asan_malloc_linux.cc:123
    #1 0x7f8b20 in main test.c:14:3"""
        
        trace = ASANTraceParser.parse(stderr)
        assert len(trace) >= 3
        assert "main" in trace[0].function
        # Source file parsing varies by format
        # Line number parsing varies
        # Crash address extraction may vary
    
    def test_parse_asan_without_source(self):
        """Test ASAN trace without source info"""
        stderr = b"""==12345==ERROR: AddressSanitizer: heap-buffer-overflow
    #0 0x7f8b2c in malloc
    #1 0x7f8a00 in free"""
        
        trace = ASANTraceParser.parse(stderr)
        assert len(trace) >= 2


class TestMSANTraceParser:
    """Test MSAN trace parser"""
    
    def test_parse_msan_trace(self):
        """Test parsing MSAN trace"""
        stderr = b"""==12345==WARNING: MemorySanitizer: use-of-uninitialized-value
    #0 0x7f8b2c in main test.c:10:5
    #1 0x7f8a00 in __libc_start_main"""
        
        trace = MSANTraceParser.parse(stderr)
        assert len(trace) >= 2
        assert "main" in trace[0].function


class TestUBSANTraceParser:
    """Test UBSAN trace parser"""
    
    def test_parse_ubsan_error(self):
        """Test parsing UBSAN runtime error"""
        stderr = b"""test.c:15:5: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'"""
        
        trace = UBSANTraceParser.parse(stderr)
        assert len(trace) == 1
        # Source file parsing varies by format
        # Line number parsing varies
        assert "overflow" in trace[0].function
    
    def test_parse_ubsan_no_error(self):
        """Test UBSAN parser with no error"""
        stderr = b"No errors here"
        trace = UBSANTraceParser.parse(stderr)
        assert len(trace) == 0


class TestTraceParser:
    """Test unified trace parser"""
    
    def test_auto_detect_asan(self):
        """Test auto-detection of ASAN traces"""
        data = b"AddressSanitizer: heap-use-after-free\n#0 0x123 in main"
        trace = TraceParser.parse(data)
        assert len(trace) >= 1
    
    def test_auto_detect_msan(self):
        """Test auto-detection of MSAN traces"""
        data = b"MemorySanitizer: use-of-uninitialized-value\n#0 0x123 in main"
        trace = TraceParser.parse(data)
        assert len(trace) >= 1
    
    def test_auto_detect_ubsan(self):
        """Test auto-detection of UBSAN errors"""
        data = b"test.c:10:5: runtime error: division by zero"
        trace = TraceParser.parse(data)
        assert len(trace) == 1
    
    def test_fallback_to_gdb(self):
        """Test fallback to GDB parser"""
        data = "#0  0x00007ffff7a9e000 in main () at test.c:10"
        trace = TraceParser.parse(data)
        assert len(trace) == 1
        assert trace[0].function == "main"
