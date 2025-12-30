"""Enhanced crash classification and exploitability analysis"""

import re
from protocrash.core.types import CrashInfo, CrashType
from protocrash.monitors.stack_trace_parser import TraceParser


class ExploitabilityAnalyzer:
    """Advanced exploitability analysis"""

    @staticmethod
    def analyze_registers(crash_info: CrashInfo) -> dict:
        """Analyze register state for control"""
        if not crash_info.stderr:
            return {'controllable': False}

        stderr_str = crash_info.stderr.decode('utf-8', errors='ignore')

        # Look for register dumps
        rip_patterns = [
            r'RIP[:=]\s*0x([0-9a-fA-F]+)',
            r'PC[:=]\s*0x([0-9a-fA-F]+)',
        ]

        for pattern in rip_patterns:
            match = re.search(pattern, stderr_str)
            if match:
                addr = match.group(1)
                # Check if address looks controllable
                if len(set(addr[-8:])) <= 2:
                    return {'controllable': True, 'register': 'RIP/PC', 'value': f"0x{addr}"}

        return {'controllable': False}

    @staticmethod
    def detect_heap_primitives(crash_info: CrashInfo) -> dict:
        """Detect heap exploitation primitives"""
        if not crash_info.stderr:
            return {'primitives': []}

        stderr_str = crash_info.stderr.decode('utf-8', errors='ignore')
        primitives = []

        if 'use-after-free' in stderr_str.lower():
            primitives.append('UAF')
        if 'double-free' in stderr_str.lower() or 'double free' in stderr_str.lower():
            primitives.append('DOUBLE_FREE')
        if 'heap-buffer-overflow' in stderr_str.lower():
            primitives.append('HEAP_OVERFLOW')

        return {'primitives': primitives}

    @staticmethod
    def analyze_control_flow(crash_info: CrashInfo) -> dict:
        """Analyze control flow hijacking potential"""
        result = {'hijackable': False, 'confidence': 'LOW'}

        if crash_info.crash_type in [CrashType.SEGV, CrashType.ILL]:
            if crash_info.stderr:
                trace = TraceParser.parse(crash_info.stderr)
                if len(trace) > 0:
                    top_func = trace[0].function if trace[0].function else ""
                    if any(kw in top_func.lower() for kw in ['call', 'jmp', 'ret']):
                        result['hijackable'] = True
                        result['confidence'] = 'MEDIUM'

        reg_analysis = ExploitabilityAnalyzer.analyze_registers(crash_info)
        if reg_analysis['controllable']:
            result['hijackable'] = True
            result['confidence'] = 'HIGH'

        return result


class CrashClassifier:
    """Classify crashes and assess exploitability"""

    EXPLOITABLE_TYPES = {CrashType.SEGV, CrashType.ABRT, CrashType.BUS}
    LIKELY_EXPLOITABLE_PATTERNS = [
        b"stack smashing detected", b"double free", b"heap-use-after-free",
        b"heap-buffer-overflow", b"stack-buffer-overflow"
    ]

    @classmethod
    def assess_exploitability(cls, crash_info: CrashInfo) -> str:
        """Assess crash exploitability with advanced analysis"""
        if not crash_info.crashed:
            return "NONE"

        analyzer = ExploitabilityAnalyzer()

        # Check for critical indicators
        reg_analysis = analyzer.analyze_registers(crash_info)
        if reg_analysis['controllable']:
            return "CRITICAL"

        cf_analysis = analyzer.analyze_control_flow(crash_info)
        if cf_analysis['hijackable'] and cf_analysis['confidence'] == 'HIGH':
            return "CRITICAL"

        heap_analysis = analyzer.detect_heap_primitives(crash_info)
        if heap_analysis['primitives']:
            if 'UAF' in heap_analysis['primitives'] or 'DOUBLE_FREE' in heap_analysis['primitives']:
                return "HIGH"

        if crash_info.crash_type in cls.EXPLOITABLE_TYPES:
            if any(pattern in crash_info.stderr for pattern in cls.LIKELY_EXPLOITABLE_PATTERNS):
                return "HIGH"
            return "MEDIUM"

        if crash_info.crash_type in [CrashType.ASAN, CrashType.MSAN]:
            if any(pattern in crash_info.stderr for pattern in cls.LIKELY_EXPLOITABLE_PATTERNS):
                return "HIGH"
            return "MEDIUM"

        if crash_info.crash_type == CrashType.ILL:
            return "LOW"
        if crash_info.crash_type == CrashType.HANG:
            return "LOW"

        return "LOW"

    @classmethod
    def generate_crash_id(cls, crash_info: CrashInfo) -> str:
        """Generate unique crash ID for deduplication"""
        import hashlib

        components = []
        if crash_info.crash_type:
            components.append(crash_info.crash_type.value)
        if crash_info.signal_number:
            components.append(str(crash_info.signal_number))

        stderr_str = crash_info.stderr.decode('utf-8', errors='ignore')
        for line in stderr_str.split('\n')[:10]:
            if 'ERROR' in line or 'Sanitizer' in line or '#' in line:
                components.append(line.strip())

        combined = '|'.join(components)
        return hashlib.md5(combined.encode()).hexdigest()[:16]
