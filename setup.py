"""
Setup script for Aruuz Python package
"""
from setuptools import setup, find_packages

setup(
    name='aruuz',
    version='0.1.0',
    description='Urdu Poetry Scansion Tool - Scans Urdu poetry into metres and feet',
    author='Your Name',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        # No dependencies for Phase 1
    ],
    entry_points={
        'console_scripts': [
            'aruuz=aruuz.cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        'aruuz': ['data/*.db'],  # For future database files
    },
)

