# Quick Start Guide

## First Time Setup

1. **Navigate to the python folder:**
   ```bash
   cd python
   ```

2. **Create and activate virtual environment:**

   **Windows:**
   ```bash
   setup_venv.bat
   ```

   **Linux/Mac:**
   ```bash
   chmod +x setup_venv.sh
   ./setup_venv.sh
   ```

3. **Verify installation:**
   ```bash
   python -c "import aruuz; print('Aruuz installed successfully!')"
   ```

## Daily Usage

1. **Activate virtual environment:**

   **Windows:**
   ```bash
   venv\Scripts\activate
   ```

   **Linux/Mac:**
   ```bash
   source venv/bin/activate
   ```

2. **Run your code:**
   ```python
   from aruuz import Scansion
   # Your code here
   ```

3. **Deactivate when done:**
   ```bash
   deactivate
   ```

## Notes

- The virtual environment folder (`venv/`) is already in `.gitignore` and won't be committed
- Always activate the virtual environment before working on the project
- The setup scripts automatically install the package in development mode

