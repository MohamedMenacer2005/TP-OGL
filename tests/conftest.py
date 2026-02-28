"""
pytest configuration for tests directory.
Adds parent directory to sys.path for src imports.
"""

import sys
from pathlib import Path

# Add parent directory (project root) to sys.path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
