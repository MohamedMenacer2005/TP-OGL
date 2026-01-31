"""
Internal test dataset - Case 1: Undefined variable bug
Validates logging of bug detection and correction
"""

def calculate_price(quantity):
    """Calculate price without tax_rate defined"""
    return quantity * tax_rate  # BUG: undefined variable
