# Crash Detection & Analysis

## Overview

Crash detection is critical for fuzzing - it identifies when the fuzzer has found a vulnerability. This document covers signal handling, sanitizers, crash triage, and analysis techniques.

---

## 1. Signal-Based Crash Detection

### Common Crash Signals

**SIGSEGV (Segmentation Fault) - Signal 11:**
- **Cause:** Invalid memory access
- **Common Scenarios:**
  - Dereferencing null pointer
  - Buffer overflow (write beyond bounds)
  - Use-after-free (accessing freed memory)
  - Stack overflow

**SIGABRT (Abort) - Signal 6:**
- **Cause:** Program called `abort()`  
- **Common Scenarios:**
  - Assertion failure
  - Double-free detected
  - Heap corruption
  - Runtime library error

**SIGILL (Illegal Instruction) - Signal 4:**
- **Cause:** Executing invalid instruction
- **Common Scenarios:**
  - Code corruption
  - Jumping to non-code memory
  - CPU instruction not supported

**SIGFPE (Floating Point Exception) - Signal 8:**
- **Cause:** Arithmetic error
- **Common Scenarios:**
  - Division by zero
  - Integer overflow (when enabled)

**SIGBUS (Bus Error) - Signal 7:**
- **Cause:** Memory alignment issue
- **Common Scenarios:**
  - Misaligned memory access
  - Hardware fault

### Implementation

```python
import signal
import subprocess
import os

class CrashDetector:
    CRASH_SIGNALS = {
        signal.SIGSEGV: "Segmentation Fault",
        signal.SIGABRT: "Abort",
        signal.SIGILL: "Illegal Instruction",
        signal.SIGFPE: "Floating Point Exception",
        signal.SIGBUS: "Bus Error",
    }
    
    def execute_and_monitor(self, target_cmd: List[str], input_data: bytes, timeout: int) -> ExecutionResult:
        """Execute target and detect crashes"""
        try:
            proc = subprocess.Popen(
                target_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            try:
                stdout, stderr = proc.communicate(input=input_data, timeout=timeout / 1000)
                exit_code = proc.returncode
                
                # Check for crash
                if exit_code < 0:
                    signal_num = -exit_code
                    if signal_num in self.CRASH_SIGNALS:
                        return ExecutionResult(
                            crashed=True,
                            signal=signal_num,
                            signal_name=self.CRASH_SIGNALS[signal_num],
                            stdout=stdout,
                            stderr=stderr
                        )
                
                return ExecutionResult(crashed=False)
                
            except subprocess.TimeoutExpired:
                # Kill entire process group
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                return ExecutionResult(crashed=False, hang=True)
                
        except Exception as e:
            return ExecutionResult(crashed=False, error=str(e))
```

---

## 2. Sanitizers

### AddressSanitizer (ASan)

**Purpose:** Detect memory errors at runtime

**Detected Issues:**
- Use-after-free
- Heap/stack/global buffer overflow
- Use-after-return
- Use-after-scope
- Memory leaks
- Initialization order bugs

**How It Works:**
- Instruments memory access at compile time
- Uses "shadow memory" to track allocation state
- Inserts red zones around allocations
- Triggers SIGABRT when error detected

**Compilation:**
```bash
# GCC/Clang
gcc -fsanitize=address -g -O1 target.c -o target

# With additional checks
gcc -fsanitize=address -fno-omit-frame-pointer -g -O1 target.c -o target
```

**Runtime Configuration:**
```bash
# Abort on first error
export ASAN_OPTIONS=abort_on_error=1

# Detailed reports
export ASAN_OPTIONS=verbosity=1:log_path=asan.log

# Detect stack-use-after-return
export ASAN_OPTIONS=detect_stack_use_after_return=1
```

**ASan Output Example:**
```
=================================================================
==12345==ERROR: AddressSanitizer: heap-use-after-free on address 0x604000000044 at pc 0x0000004008ef
READ of size 4 at 0x604000000044 thread T0
    #0 0x4008ee in main /path/to/target.c:10
    #1 0x7f0f3d1c0c86 in __libc_start_main
    #2 0x400759 in _start

0x604000000044 is located 4 bytes inside of 400-byte region [0x604000000040,0x6040000001d0)
freed by thread T0 here:
    #0 0x7f0f3d6a4e37 in __interceptor_free.part.0
    #1 0x4008d5 in main /path/to/target.c:9
```

---

### MemorySanitizer (MSan)

**Purpose:** Detect use of uninitialized memory

**How It Works:**
- Tracks initialization status of every byte
- Operates at bit-level granularity
- Reports when uninitialized data is used in conditional or memory access

**Compilation:**
```bash
clang -fsanitize=memory -fno-omit-frame-pointer -g -O2 target.c -o target
```

**Important:** ALL code must be instrumented (including libraries)

**MSan Output Example:**
```
==18467== WARNING: MemorySanitizer: use-of-uninitialized-value
    #0 0x4940a4 in main /path/to/target.c:15
    #1 0x7f2d1c3c7c86 (/lib/x86_64-linux-gnu/libc.so.6+0x21c86)

  Uninitialized value was created by a heap allocation
    #0 0x493d03 in malloc
    #1 0x493fe8 in main /path/to/target.c:12
```

---

### UndefinedBehaviorSanitizer (UBSan)

**Purpose:** Detect undefined behavior

**Detected Issues:**
- Integer overflow
- Null pointer dereference
- Misaligned pointer access
- Signed integer overflow
- Division by zero

**Compilation:**
```bash
gcc -fsanitize=undefined -g target.c -o target
```

---

## 3. Crash Triage

### Crash Deduplication

**Problem:** Fuzzer finds thousands of crashes, many duplicates

**Solution:** Group similar crashes by:
1. **Signal type** (SIGSEGV, SIGABRT, etc.)
2. **Crash location** (program counter, function name)
3. **Stack trace hash**

**Implementation:**
```python
import hashlib

def crash_hash(stack_trace: str) -> str:
    """Generate unique hash for crash"""
    # Extract function names from stack trace
    functions = []
    for line in stack_trace.split('\n'):
        if '#' in line and 'in ' in line:
            # Extract function name
            func = line.split(' in ')[1].split(' ')[0]
            functions.append(func)
    
    # Hash top 5 functions
    key = '|'.join(functions[:5])
    return hashlib.md5(key.encode()).hexdigest()

def bucket_crashes(crashes: List[Crash]) -> Dict[str, List[Crash]]:
    """Group similar crashes"""
    buckets = {}
    
    for crash in crashes:
        # Create bucket key
        key = f"{crash.signal}:{crash_hash(crash.stack_trace)}"
        
        if key not in buckets:
            buckets[key] = []
        
        buckets[key].append(crash)
    
    return buckets
```

---

### Stack Trace Parsing

**GDB Integration:**
```python
def get_stack_trace(core_file: str, binary: str) -> str:
    """Extract stack trace from core dump"""
    gdb_cmd = [
        'gdb',
        '--batch',
        '--quiet',
        '-ex', 'bt',  # backtrace
        binary,
        core_file
    ]
    
    result = subprocess.run(gdb_cmd, capture_output=True, text=True)
    return result.stdout
```

**Parse Stack Trace:**
```python
def parse_stack_trace(trace: str) -> List[StackFrame]:
    """Parse GDB backtrace output"""
    frames = []
    
    for line in trace.split('\n'):
        if line.startswith('#'):
            parts = line.split()
            frame_num = int(parts[0][1:])  # Remove '#'
            
            # Extract address, function, file, line
            address = parts[1] if len(parts) > 1 else None
            function = parts[3] if 'in' in parts else None
            
            frames.append(StackFrame(
                number=frame_num,
                address=address,
                function=function,
                location=parse_location(line)
            ))
    
    return frames
```

---

## 4. Crash Minimization

**Goal:** Reduce crash input to minimal size while preserving crash

**Algorithm:**
```python
def minimize_crash(original_input: bytes, target_cmd: List[str], timeout: int) -> bytes:
    """Binary search minimization"""
    current = original_input
    
    # Try removing chunks
    for chunk_size in [len(current) // 2, len(current) // 4, len(current) // 8, 1]:
        pos = 0
        while pos < len(current):
            # Try removing chunk
            candidate = current[:pos] + current[pos + chunk_size:]
            
            # Test if still crashes
            result = execute_and_monitor(target_cmd, candidate, timeout)
            
            if result.crashed and result.signal == original_signal:
                # Crash preserved, keep smaller input
                current = candidate
            else:
                # Crash lost, try next position
                pos += chunk_size
    
    return current
```

---

## 5. Exploitability Analysis

**Categorize Crash Severity:**

**1. NULL Dereference:**
- Low exploitability
- Usually causes simple crash

**2. Stack Buffer Overflow:**
- High exploitability
- Can overwrite return address
- Potential RCE

**3. Heap Corruption:**
- Medium-High exploitability
- Can overwrite function pointers
- Complex to exploit

**4. Use-After-Free:**
- High exploitability
- Can control freed memory
- Common in modern exploits

**Implementation:**
```python
def analyze_exploitability(crash: Crash) -> str:
    """Estimate crash exploitability"""
    
    # Check signal
    if crash.signal == signal.SIGABRT:
        return "LOW"  # Usually assertion/double-free
    
    # Check crash location
    if "null" in crash.stack_trace.lower():
        return "LOW"  # NULL deref
    
    # Check for heap
    if "malloc" in crash.stack_trace or "free" in crash.stack_trace:
        return "MEDIUM-HIGH"  # Heap corruption
    
    # Check for stack
    if "stack" in crash.stack_trace.lower():
        return "HIGH"  # Stack overflow
    
    # Default
    return "MEDIUM"
```

---

## 6. Fuzzing with Sanitizers

**Best Practices:**

1. **ASan for most bugs:**
   ```bash
   export ASAN_OPTIONS=abort_on_error=1:detect_leaks=0
   protocrash fuzz --target ./target_asan --corpus ./seeds
   ```

2. **MSan for uninitialized memory:**
   ```bash
   protocrash fuzz --target ./target_msan --corpus ./seeds
   ```

3. **Rotate sanitizers:**
   - Day 1: ASan
   - Day 2: MSan
   - Day 3: UBSan
   - Maximize bug diversity

---

## Performance Impact

**Sanitizer Overhead:**
- ASan: ~2x slowdown
- MSan: ~3x slowdown
- UBSan: ~1.5x slowdown

**Recommendation:** Use sanitizers despite overhead - bugs found are worth it!

---

Status: Comprehensive crash detection documentation complete
