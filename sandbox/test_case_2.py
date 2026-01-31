"""
Internal test dataset - Case 2: Missing error handling
Validates robustness logging
"""

def load_data(filename):
    """Load data without error handling"""
    with open(filename) as f:  # BUG: no try/except
        return f.read()
