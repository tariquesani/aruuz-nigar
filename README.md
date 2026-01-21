# Aruuz Nigar - Urdu Poetry Scansion Tool

## What is Aruuz Nigar?

Aruuz Nigar is an Urdu poetry scansion tool that helps poets and readers understand Urdu arūz by inferring the taqti of individual lines and matching them against known bahrs. It consists of two parts: **Aruuz**, a reusable Python library that performs the scansion and meter analysis, and **Nigar**, a Flask based web frontend that provides a basic interface for end-users.

## Why create Aruuz Nigar?

Aruuz Nigar was created for my understanding of Urdu arūz. While tools such as Rekhta's taqti and Aruuz.com are available, Rekhta is proprietary and the publicly available Aruuz.com codebase is more than a decade old, written in C#. Aruuz Nigar aims to provide a modern, open source, developer friendly alternative with a clear semantic core that can run on both desktops and servers.

## How to use Aruuz Nigar?

### For Windows end-users

Download the executable server file from [Coming Soon], Unzip it in a folder. Double click on `aruuznigar.exe`. A browser with the Web interface will launch, if it doesn't, open `127.0.0.1:5000` in your browser.

**Note**: The Windows executable runs a local Flask web server and opens the interface in your browser.
All processing happens locally on your machine, and no external network access is required.

### For everyone else

**Installation:**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tariquesani/aruuz-nigar.git
   cd aruuz-nigar/
   ```

2. **Setup Virtual Environment**

   **Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install --upgrade pip
   pip install -e .
   pip install -r requirements.txt
   ```

   **Linux/Mac:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -e .
   pip install -r requirements.txt
   ```

3. **Run the Flask web application (Nigar):**
   ```bash
   python app.py
   ```
   Then open your browser to: `http://127.0.0.1:5000`

   The web app provides:
   - RTL (right-to-left) text input for Urdu poetry
   - RTL display of scansion codes
   - Meter matching and identification

4. **For developers, use as a Python library (Aruuz):**

   ```python
   from aruuz.scansion import Scansion
   from aruuz.models import Lines

   scanner = Scansion()
   line = Lines("نقش فریادی ہے کس کی شوخیِ تحریر کا")
   scanner.add_line(line)
   results = scanner.scan_lines()
   ```

## Project Structure

- `aruuz/` - Main package (Aruuz library)
  - `scansion/` - Core scansion engine modules
    - `core.py` - Main scansion engine
    - `word_analysis.py` - Word-level analysis
    - `word_scansion_assigner.py` - Word scansion assignment
    - `code_assignment.py` - Code assignment logic
    - `length_scanners.py` - Length scanning functions
    - `meter_matching.py` - Meter matching algorithms
    - `prosodic_rules.py` - Prosodic rules and adjustments
    - `scoring.py` - Scoring mechanisms
    - `explanation_builder.py` - Explanation generation
  - `tree/` - Pattern matching trees
    - `code_tree.py` - Code tree implementation
    - `pattern_tree.py` - Pattern tree matching
    - `state_machine.py` - State machine for pattern matching
  - `database/` - Database functionality
    - `word_lookup.py` - Word lookup from database
    - `aruuz_nigar.db` - SQLite database
  - `utils/` - Utility functions
    - `text.py` - Text processing utilities
    - `araab.py` - Diacritical marks handling
    - `logging_config.py` - Logging configuration
  - `meters.py` - Meter definitions (bahrs)
  - `models.py` - Data models (Lines, Words, etc.)
- `app.py` - Flask web application (Nigar frontend)
- `templates/` - Flask HTML templates
  - `index.html` - Main interface
- `static/` - Static web assets (CSS, etc.)
- `scripts/` - CLI scripts and utilities
  - `scan_poetry.py` - Poetry scanning script
  - `scan_word.py` - Word scanning script
- `tests/` - Test suite
  - `legacy/` - Legacy test files
  - `test_canonical_sher_to_bahr_mapping.py` - Canonical test mappings
- `docs/` - Documentation files
- `setup.py` - Package setup configuration
- `requirements.txt` - Python dependencies


## Notes

Word-level scansion intentionally over-generates. Canonical selection happens at line/meter level.

## Attribution

Based on the original [Aruuz](https://github.com/sayedzeeshan/Aruuz) by [Sayed Zeeshan Asghar](https://github.com/sayedzeeshan) (thank you!)
Original: GPL-2.0 licensed  
Aruuz Nigar Python port: GPL-3.0 licensed  
Ported by Dr. Tarique Sani, 2026

## Status

**In Development** 
- Works well for regular meters (bahr)
- Will work with some caveats for bahr-e-hindi and bahr-e-zamzama
- Does not support Rubai well

**Bug Reports and Feedback very welcome**

Aruuz Nigar is under active development, and bugs or incorrect scansion results are expected.
If you encounter issues, please report them using [GitHub Issues](https://github.com/tariquesani/aruuz-nigar/issues).

## Documentation
The core Python library (`aruuz/`) is extensively documented using module-level docstrings and inline explanations for all public classes and functions. These docstrings describe the intended behavior, inputs, outputs, and design rationale of the scansion engine, meter matching, tree traversal, scoring, and utility modules.

The existing source documentation is suitable for automatic API documentation generation using tools such as Sphinx or similar docstring-based systems. Generated API documentation is not published yet and will be added once the public interfaces stabilize further.


## License

GPL V3.0, See [LICENSE](./LICENSE) file in parent directory.
