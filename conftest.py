"""
Pytest configuration file.
Sets up the Python path and provides shared fixtures.
"""

import sys
import os
from pathlib import Path

# Add the project root to sys.path to ensure 'src' module can be imported
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure environment for testing
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')


def pytest_configure(config):
    """pytest hook: called before test collection begins."""
    pass
