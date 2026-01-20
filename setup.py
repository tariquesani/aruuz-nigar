"""
Setup script for Aruuz Python package
"""
from setuptools import setup, find_packages

setup(
    name='aruuz',
    version='0.1.0',
    description='Urdu Poetry Scansion Tool - Scans Urdu poetry into metres and feet',
    author='Dr. Tarique Sani',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        # Core library has no external dependencies
        # Flask is used for the web app (app.py) but is installed separately via requirements.txt
    ],
    # Entry point removed - aruuz.cli module doesn't exist yet
    # entry_points={
    #     'console_scripts': [
    #         'aruuz=aruuz.cli:main',
    #     ],
    # },
    include_package_data=True,
    package_data={
        'aruuz': ['database/*.db'],  # Database files in database/ directory
    },
)

