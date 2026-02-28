"""Add sandbox/test_local to sys.path so tests can import local modules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
