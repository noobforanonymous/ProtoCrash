# Days 6-7 - Development Environment Setup

**Phase:** Foundation  
**Focus:** Python development environment and tooling

---

## Goals

- Set up Python package structure
- Configure pytest framework
- Set up linting (ruff, black, mypy)
- Create pre-commit hooks
- Add type hints configuration
- Create development documentation

---

## Python Package Structure

### Directory Layout

```
ProtoCrash/
├── setup.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── .pre-commit-config.yaml
├── mypy.ini
├── .ruff.toml
├── src/
│   └── protocrash/
│       ├── __init__.py
│       ├── __version__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   └── main.py
│       ├── fuzzing_engine/
│       │   ├── __init__.py
│       │   ├── fuzzer.py
│       │   ├── queue.py
│       │   └── corpus.py
│       ├── mutators/
│       │   ├── __init__.py
│       │   ├── mutation_engine.py
│       │   ├── deterministic.py
│       │   ├── havoc.py
│       │   ├── dictionary.py
│       │   └── splice.py
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── protocol_parser.py
│       │   ├── http_parser.py
│       │   ├── dns_parser.py
│       │   ├── smtp_parser.py
│       │   └── binary_parser.py
│       ├── monitors/
│       │   ├── __init__.py
│       │   ├── coverage.py
│       │   ├── crash_detector.py
│       │   └── sanitizers.py
│       ├── reporters/
│       │   ├── __init__.py
│       │   ├── crash_reporter.py
│       │   └── stats.py
│       └── core/
│           ├── __init__.py
│           ├── config.py
│           └── types.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_mutators/
    ├── test_parsers/
    ├── test_coverage/
    └── test_integration/
```

---

## Configuration Files

### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "protocrash"
version = "0.1.0"
description = "Coverage-guided protocol fuzzer"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
    "pwntools>=4.10.0",
    "scapy>=2.5.0",
    "psutil>=5.9.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "black>=23.0.0",
    "mypy>=1.5.0",
    "pre-commit>=3.4.0",
]

[project.scripts]
protocrash = "protocrash.cli.main:cli"

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 100
target-version = ["py311"]
include = '\.pyi?$'

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "W", "C90", "I", "N", "UP", "B", "A", "C4", "PIE", "T20", "SIM"]
ignore = []

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=src/protocrash --cov-report=html --cov-report=term"
```

### requirements-dev.txt

```
# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-timeout>=2.1.0

# Code quality
ruff>=0.1.0
black>=23.0.0
mypy>=1.5.0
pre-commit>=3.4.0

# Type stubs
types-PyYAML>=6.0.0
types-psutil>=5.9.0
```

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.10.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.5
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict]
```

---

## Testing Framework

### pytest Configuration

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=src/protocrash
    --cov-report=html
    --cov-report=term-missing
    --cov-report=xml
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

### Test Structure

**tests/conftest.py:**
```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_http_request():
    return b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"

@pytest.fixture
def sample_dns_query():
    return b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'

@pytest.fixture
def temp_corpus(tmp_path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    return corpus_dir

@pytest.fixture
def temp_crashes(tmp_path):
    crash_dir = tmp_path / "crashes"
    crash_dir.mkdir()
    return crash_dir
```

---

## Code Quality Tools

### Ruff (Linting)

**.ruff.toml:**
```toml
line-length = 100
target-version = "py311"

select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "A",   # flake8-builtins
    "C4",  # flake8-comprehensions
    "PIE", # flake8-pie
    "T20", # flake8-print
    "SIM", # flake8-simplify
]

ignore = [
    "E501",  # line too long (handled by black)
]

[per-file-ignores]
"tests/*" = ["T20"]  # Allow print in tests
```

### Black (Formatting)

```bash
black src/ tests/ --line-length 100
```

### Mypy (Type Checking)

**mypy.ini:**
```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
strict_equality = True

[mypy-scapy.*]
ignore_missing_imports = True

[mypy-pwntools.*]
ignore_missing_imports = True
```

---

## Development Workflow

### 1. Install Development Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### 2. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_mutators/test_deterministic.py

# Run marked tests
pytest -m unit
pytest -m integration
```

### 3. Code Quality Checks

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/

# Run all checks (pre-commit)
pre-commit run --all-files
```

### 4. Manual Testing

```bash
# Install package
pip install -e .

# Run CLI
protocrash --help
protocrash fuzz --target ./test_target --corpus ./seeds
```

---

## CI/CD Configuration

### GitHub Actions (.github/workflows/test.yml)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
    
    - name: Lint with ruff
      run: |
        ruff check src/ tests/
    
    - name: Format check with black
      run: |
        black --check src/ tests/
    
    - name: Type check with mypy
      run: |
        mypy src/
    
    - name: Test with pytest
      run: |
        pytest --cov --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## Next Steps

- Create initial package structure
- Set up all configuration files
- Install development dependencies
- Configure pre-commit hooks
- Write first basic tests
- Verify development workflow

---

Status: Development environment specification complete, ready for setup
