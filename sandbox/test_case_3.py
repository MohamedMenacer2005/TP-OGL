"""
Internal test dataset - Case 3: Division by zero
Validates fix validation through Judge
"""

def divide_numbers(a, b):
    """Divide without zero check"""
    return a / b  # BUG: division by zero not handled
