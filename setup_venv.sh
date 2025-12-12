#!/bin/bash
# Setup script for creating virtual environment on Unix/Linux/Mac

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing package in development mode..."
pip install -e .

echo ""
echo "Virtual environment setup complete!"
echo "To activate: source venv/bin/activate"
echo "To deactivate: deactivate"

