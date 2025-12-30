# Crash Detector - Component Specification

## Overview

The crash detector monitors target execution for crashes, handles different crash signals, integrates with sanitizers, and performs crash triage and minimization.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│          Crash Detector                     │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐    ┌───────────────────┐ │
│  │    Signal    │    │    Sanitizer      │ │
│  │    Handler   │    │    Monitor        │ │
│  └──────────────┘    └───────────────────┘ │
│         │                     │             │
│         ▼                     ▼             │
│  ┌─────────────────────────────────────┐   │
│  │        Crash Classifier             │   │
│  └─────────────────────────────────────┘   │
│         │                                   │
│         ▼                                   │
│  ┌─────────────────────────────────────┐   │
│  │        Crash Minimizer              │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Class Design

### 1. CrashDetector (Main Class)

```python
import subprocess
import signal
import os
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

class CrashType(Enum):
    """Types of crashes"""
    SEGV = "Segmentation Fault"
    ABRT = "Abort"
    ILL = "Illegal Instruction"
    FPE = "Floating Point Exception"
    BUS = "Bus Error"
    HANG = "Timeout/Hang"
    ASAN = "AddressSanitizer"
    MSAN = "MemorySanitizer"
    UBSAN = "UndefinedBehaviorSanitizer"

@dataclass
class CrashInfo:
    """Information about a crash"""
    crashed: bool
    crash_type: Optional[CrashType] = None
    signal_number: Optional[int] = None
    exit_code: int = 0
    stdout: bytes = b""
    stderr: bytes = b""
    stack_trace: Optional[str] = None
    exploitability: Optional[str] = None
    input_data: Optional[bytes] = None
    
class CrashDetector:
    """Main crash detection interface"""
    
    CRASH_SIGNALS = {
        signal.SIGSEGV: CrashType.SEGV,
        signal.SIGABRT: CrashType.ABRT,
        signal.SIGILL: CrashType.ILL,
        signal.SIGFPE: CrashType.FPE,
        signal.SIGBUS: CrashType.BUS,
    }
    
    def __init__(self, timeout_ms: int = 5000, enable_asan: bool = True):
        """
        Initialize crash detector
        
        Args:
            timeout_ms: Execution timeout in milliseconds
            enable_asan: Enable AddressSanitizer detection
        """
        self.timeout_ms = timeout_ms
        self.enable_asan = enable_asan
        
        self.signal_handler = SignalHandler()
        self.sanitizer_monitor = SanitizerMonitor()
        self.classifier = CrashClassifier()
        self.minimizer = CrashMinimizer(self)
        
        # Setup environment for sanitizers
        if enable_asan:
            self._setup_asan_env()
    
    def execute_and_detect(self, target_cmd: List[str], input_data: bytes) -> CrashInfo:
        """
        Execute target and detect crashes
        
        Args:
            target_cmd: Command to execute target
            input_data: Input data to feed to target
            
        Returns:
            CrashInfo object
        """
        try:
            proc = subprocess.Popen(
                target_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            try:
                stdout, stderr = proc.communicate(
                    input=input_data,
                    timeout=self.timeout_ms / 1000
                )
                exit_code = proc.returncode
                
                # Check for crash
                crash_info = self._analyze_execution(
                    exit_code, stdout, stderr, input_data
                )
                
                return crash_info
                
            except subprocess.TimeoutExpired:
                # Hang detected
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                return CrashInfo(
                    crashed=True,
                    crash_type=CrashType.HANG,
                    input_data=input_data
                )
                
        except Exception as e:
            return CrashInfo(
                crashed=False,
                stderr=str(e).encode()
            )
    
    def _analyze_execution(self, exit_code: int, stdout: bytes, stderr: bytes, input_data: bytes) -> CrashInfo:
        """Analyze execution result"""
        
        # Check for signal-based crash
        if exit_code < 0:
            signal_num = -exit_code
            if signal_num in self.CRASH_SIGNALS:
                crash_type = self.CRASH_SIGNALS[signal_num]
                
                return CrashInfo(
                    crashed=True,
                    crash_type=crash_type,
                    signal_number=signal_num,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    input_data=input_data
                )
        
        # Check for sanitizer crash
        if self.enable_asan:
            san_crash = self.sanitizer_monitor.check_sanitizer_crash(stderr)
            if san_crash:
                return CrashInfo(
                    crashed=True,
                    crash_type=san_crash,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    stack_trace=self.sanitizer_monitor.extract_stack_trace(stderr),
                    input_data=input_data
                )
        
        # No crash
        return CrashInfo(
            crashed=False,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr
        )
    
    def _setup_asan_env(self):
        """Setup ASan environment variables"""
        os.environ['ASAN_OPTIONS'] = 'abort_on_error=1:detect_leaks=0'
```

---

### 2. SignalHandler

```python
import signal

class SignalHandler:
    """Handle Unix signals for crash detection"""
    
    @staticmethod
    def signal_to_string(sig_num: int) -> str:
        """Convert signal number to name"""
        signal_names = {
            signal.SIGSEGV: "SIGSEGV (Segmentation Fault)",
            signal.SIGABRT: "SIGABRT (Abort)",
            signal.SIGILL: "SIGILL (Illegal Instruction)",
            signal.SIGFPE: "SIGFPE (Floating Point Exception)",
            signal.SIGBUS: "SIGBUS (Bus Error)",
            signal.SIGTRAP: "SIGTRAP (Trace/Breakpoint Trap)",
        }
        
        return signal_names.get(sig_num, f"Signal {sig_num}")
    
    @staticmethod
    def is_crash_signal(sig_num: int) -> bool:
        """Check if signal indicates crash"""
        crash_signals = {
            signal.SIGSEGV,
            signal.SIGABRT,
            signal.SIGILL,
            signal.SIGFPE,
            signal.SIGBUS,
        }
        
        return sig_num in crash_signals
```

---

### 3. SanitizerMonitor

```python
import re

class SanitizerMonitor:
    """Monitor for sanitizer crashes"""
    
    ASAN_PATTERN = re.compile(b'AddressSanitizer')
    MSAN_PATTERN = re.compile(b'MemorySanitizer')
    UBSAN_PATTERN = re.compile(b'UndefinedBehaviorSanitizer')
    
    def check_sanitizer_crash(self, stderr: bytes) -> Optional[CrashType]:
        """Check if crash is from sanitizer"""
        
        if self.ASAN_PATTERN.search(stderr):
            return CrashType.ASAN
        elif self.MSAN_PATTERN.search(stderr):
            return CrashType.MSAN
        elif self.UBSAN_PATTERN.search(stderr):
            return CrashType.UBSAN
        
        return None
    
    def extract_stack_trace(self, stderr: bytes) -> str:
        """Extract stack trace from sanitizer output"""
        try:
            text = stderr.decode('utf-8', errors='ignore')
            
            # Find stack trace section
            lines = text.split('\n')
            stack_lines = []
            in_stack = False
            
            for line in lines:
                if '#0' in line or 'backtrace:' in line.lower():
                    in_stack = True
                
                if in_stack:
                    if line.strip().startswith('#'):
                        stack_lines.append(line)
                    elif stack_lines and not line.strip():
                        break
            
            return '\n'.join(stack_lines)
            
        except Exception:
            return ""
    
    def parse_asan_error(self, stderr: bytes) -> Dict:
        """Parse ASan error details"""
        text = stderr.decode('utf-8', errors='ignore')
        
        error_info = {
            'type': 'unknown',
            'address': None,
            'size': None
        }
        
        # Parse error type
        if 'heap-use-after-free' in text:
            error_info['type'] = 'use-after-free'
        elif 'heap-buffer-overflow' in text:
            error_info['type'] = 'heap-overflow'
        elif 'stack-buffer-overflow' in text:
            error_info['type'] = 'stack-overflow'
        elif 'global-buffer-overflow' in text:
            error_info['type'] = 'global-overflow'
        
        # Parse address
        addr_match = re.search(r'0x[0-9a-f]+', text)
        if addr_match:
            error_info['address'] = addr_match.group(0)
        
        return error_info
```

---

### 4. CrashClassifier

```python
class CrashClassifier:
    """Classify crashes by type and exploitability"""
    
    def classify_exploitability(self, crash: CrashInfo) -> str:
        """
        Estimate crash exploitability
        
        Returns:
            'HIGH', 'MEDIUM', 'LOW', 'NONE'
        """
        if not crash.crashed:
            return 'NONE'
        
        # NULL dereference - usually low
        if crash.stderr and b'null' in crash.stderr.lower():
            return 'LOW'
        
        # Abort - usually assertion, low exploitability
        if crash.crash_type == CrashType.ABRT:
            return 'LOW'
        
        # Heap corruption - high exploitability
        if crash.stderr and b'heap' in crash.stderr.lower():
            if b'use-after-free' in crash.stderr.lower():
                return 'HIGH'
            else:
                return 'MEDIUM-HIGH'
        
        # Stack overflow - high exploitability
        if crash.stderr and b'stack' in crash.stderr.lower():
            return 'HIGH'
        
        # Default
        if crash.crash_type == CrashType.SEGV:
            return 'MEDIUM'
        
        return 'LOW'
    
    def generate_crash_hash(self, crash: CrashInfo) -> str:
        """Generate unique hash for crash deduplication"""
        import hashlib
        
        # Use crash type + stack trace for hash
        hash_input = f"{crash.crash_type.name}"
        
        if crash.stack_trace:
            # Use top 5 stack frames
            frames = crash.stack_trace.split('\n')[:5]
            hash_input += '|'.join(frames)
        
        return hashlib.md5(hash_input.encode()).hexdigest()
```

---

### 5. CrashMinimizer

```python
class CrashMinimizer:
    """Minimize crash inputs to smallest size"""
    
    def __init__(self, detector: CrashDetector):
        self.detector = detector
    
    def minimize(self, target_cmd: List[str], crash_input: bytes, max_iterations: int = 100) -> bytes:
        """
        Minimize crash input using binary search
        
        Args:
            target_cmd: Target command
            crash_input: Original crash input
            max_iterations: Maximum minimization attempts
            
        Returns:
            Minimized input that still triggers crash
        """
        current = crash_input
        original_crash = self.detector.execute_and_detect(target_cmd, crash_input)
        
        if not original_crash.crashed:
            return current
        
        original_signal = original_crash.signal_number
        iterations = 0
        
        # Try removing chunks of different sizes
        for chunk_size in self._get_chunk_sizes(len(current)):
            if iterations >= max_iterations:
                break
            
            pos = 0
            while pos < len(current) and iterations < max_iterations:
                # Try removing chunk
                candidate = current[:pos] + current[pos + chunk_size:]
                
                if len(candidate) == 0:
                    pos += chunk_size
                    continue
                
                # Test if still crashes
                result = self.detector.execute_and_detect(target_cmd, candidate)
                iterations += 1
                
                if result.crashed and result.signal_number == original_signal:
                    # Crash preserved, use smaller input
                    current = candidate
                else:
                    # Crash lost, try next position
                    pos += chunk_size
        
        return current
    
    def _get_chunk_sizes(self, length: int) -> List[int]:
        """Calculate chunk sizes for minimization"""
        sizes = []
        
        # Start with large chunks, then smaller
        for divisor in [2, 4, 8, 16, 32]:
            size = max(length // divisor, 1)
            if size not in sizes:
                sizes.append(size)
        
        # Always try single byte
        if 1 not in sizes:
            sizes.append(1)
        
        return sizes
```

---

### 6. CrashReporter

```python
from datetime import datetime
import json

class CrashReporter:
    """Generate crash reports"""
    
    def generate_report(self, crash: CrashInfo, crash_id: str) -> Dict:
        """Generate structured crash report"""
        
        report = {
            'crash_id': crash_id,
            'timestamp': datetime.now().isoformat(),
            'crashed': crash.crashed,
            'crash_type': crash.crash_type.value if crash.crash_type else None,
            'signal': crash.signal_number,
            'exit_code': crash.exit_code,
            'exploitability': crash.exploitability,
            'stack_trace': crash.stack_trace,
            'stderr_snippet': crash.stderr[:500].decode('utf-8', errors='ignore') if crash.stderr else None,
            'input_size': len(crash.input_data) if crash.input_data else 0,
        }
        
        return report
    
    def save_crash(self, crash: CrashInfo, output_dir: str, crash_id: str):
        """Save crash to disk"""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save input
        input_path = os.path.join(output_dir, f"{crash_id}.input")
        with open(input_path, 'wb') as f:
            f.write(crash.input_data)
        
        # Save report
        report = self.generate_report(crash, crash_id)
        report_path = os.path.join(output_dir, f"{crash_id}.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save stderr if interesting
        if crash.stderr:
            stderr_path = os.path.join(output_dir, f"{crash_id}.stderr")
            with open(stderr_path, 'wb') as f:
                f.write(crash.stderr)
```

---

## Usage Example

```python
# Initialize crash detector
detector = CrashDetector(timeout_ms=5000, enable_asan=True)

# Execute target
crash_info = detector.execute_and_detect(
    target_cmd=['./vulnerable_server'],
    input_data=b"GET /" + b"A" * 10000 + b" HTTP/1.1\r\n\r\n"
)

if crash_info.crashed:
    # Classify exploitability
    classifier = CrashClassifier()
    crash_info.exploitability = classifier.classify_exploitability(crash_info)
    
    # Minimize input
    minimizer = CrashMinimizer(detector)
    minimized = minimizer.minimize(
        target_cmd=['./vulnerable_server'],
        crash_input=crash_info.input_data
    )
    
    # Save crash
    reporter = CrashReporter()
    crash_hash = classifier.generate_crash_hash(crash_info)
    reporter.save_crash(crash_info, './crashes', crash_hash)
    
    print(f"Crash found! Type: {crash_info.crash_type.value}")
    print(f"Exploitability: {crash_info.exploitability}")
    print(f"Minimized from {len(crash_info.input_data)} to {len(minimized)} bytes")
```

---

## Performance Targets

- **Signal Detection:** < 1ms overhead
- **Sanitizer Parsing:** < 10ms
- **Crash Minimization:** < 30 seconds per crash
- **Report Generation:** < 100ms

---

Status: Crash detector specification complete
