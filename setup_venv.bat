@echo off
REM Setup script for creating virtual environment on Windows

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing package in development mode...
pip install -e .

echo.
echo Virtual environment setup complete!
echo To activate: venv\Scripts\activate
echo To deactivate: deactivate

