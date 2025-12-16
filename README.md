# Aruuz Nigar - Urdu Poetry Scansion Tool

A Python tool and library for scanning Urdu poetry into metres and feet (prosody/taqti analysis).

## Phase 1: Core Engine (Heuristics Only)

This is the initial implementation using heuristics-based word code assignment without database lookup.

## Project Structure

- `aruuz/` - Main package
  - `scansion.py` - Core scansion engine
  - `meters.py` - Meter definitions
  - `models.py` - Data models
  - `utils/` - Utility functions
  - `tree/` - Pattern matching trees
- `tests/` - Test suite
- `scripts/` - CLI scripts
- `examples/` - Sample poetry for testing

## Installation 

### Setup Virtual Environment

**Windows:**
```bash
# Run the setup script
setup_venv.bat

# Or manually:
python -m venv venv
venv\bin\activate
pip install --upgrade pip
pip install -e .
```

**Linux/Mac:**
```bash
# Run the setup script
chmod +x setup_venv.sh
./setup_venv.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .
```

### Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### Deactivate Virtual Environment

```bash
deactivate
```

## Usage

```python
from aruuz import Scansion

scanner = Scansion()
scanner.add_line("نقش فریادی ہے کس کی شوخیِ تحریر کا")
results = scanner.scan_lines()
```

## Testing

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

### Run Tests

```bash
# Run all tests (verbose by default via pytest.ini)
pytest

# Run with extra verbose output (shows more details)
pytest -vv

# Run specific test file
pytest tests/test_taqti.py

# Run specific test class
pytest tests/test_taqti.py::TestTaqtiRealWords

# Run specific test method
pytest tests/test_taqti.py::TestTaqtiLengthTwo::test_starts_with_alif_madd

# View test collection with docstrings (shows what tests will run)
pytest --collect-only -v

# Run with coverage (if pytest-cov is installed)
pytest --cov=aruuz tests/
```

**Viewing Test Docstrings:**

Test docstrings contain detailed descriptions of what each test verifies.
To see them:

```bash
# View all tests with their docstrings
pytest --collect-only -v

# View specific test's docstring
pytest --collect-only -v tests/test_taqti.py::TestTaqtiLengthTwo::test_starts_with_alif_madd
```

Docstrings are also visible in:
- **IDE test runners** (VS Code, PyCharm, etc.) - hover over test names or view test explorer
- **HTML reports**: `pytest --html=report.html` (requires `pip install pytest-html`)
- **When tests fail** - docstrings appear in traceback output

## Attribution

Based on Aruuz by Sayed Zeeshan Asghar  
Original: GPL-2.0 licensed  
Aruuz Nigar Python port: GPL-3.0 licensed  
Ported by Dr. Tarique Sani, 2025

## Status

🚧 **In Development** - Phase 1 (Heuristics Only)

## License

See LICENSE file in parent directory.

