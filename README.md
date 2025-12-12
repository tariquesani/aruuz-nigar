# Aruuz Nigar - Urdu Poetry Scansion Tool

A Python tool and library for scanning Urdu poetry into metres and feet (parsody/taqti analysis).

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

## Status

🚧 **In Development** - Phase 1 (Heuristics Only)

## License

See LICENSE file in parent directory.

