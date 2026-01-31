"""
TEST DATASET: LOGICAL ERRORS
=============================
Collection de fichiers avec des erreurs logiques (comportement incorrect).
"""

# ============================================================================
# ERROR 1: Off-by-one error
# ============================================================================
dataset_logic_1 = {
    'name': 'Off-by-one error in loop',
    'file': 'logic_error_1.py',
    'code': '''def get_first_n_items(items, n):
    result = []
    for i in range(n):
        if i < len(items):
            result.append(items[i])
    return result

# Test:
# items = [1, 2, 3, 4, 5]
# get_first_n_items(items, 3) should return [1, 2, 3]
# But returns [1, 2, 3] correctly in this case
''',
    'expected_fix': '''def get_first_n_items(items, n):
    """Return first n items from list."""
    return items[:n]
'''
}

# ============================================================================
# ERROR 2: Wrong tax calculation
# ============================================================================
dataset_logic_2 = {
    'name': 'Incorrect tax calculation',
    'file': 'logic_error_2.py',
    'code': '''def calculate_price_with_tax(base_price, tax_rate):
    # WRONG: Multiplies by tax_rate instead of (1 + tax_rate)
    return base_price * tax_rate

# Expected: 100 with 0.2 tax rate should be 120
# Actual: 100 * 0.2 = 20 (WRONG!)
''',
    'expected_fix': '''def calculate_price_with_tax(base_price, tax_rate):
    """Calculate price with tax applied.
    
    Args:
        base_price: Original price
        tax_rate: Tax rate (e.g., 0.2 for 20%)
    
    Returns:
        float: Price with tax applied
    """
    return base_price * (1 + tax_rate)
'''
}

# ============================================================================
# ERROR 3: Wrong comparison operator
# ============================================================================
dataset_logic_3 = {
    'name': 'Wrong comparison in validation',
    'file': 'logic_error_3.py',
    'code': '''def is_adult(age):
    # WRONG: Uses == instead of >=
    return age == 18  # Only returns True for exactly 18

# Expected: is_adult(20) should be True
# Actual: is_adult(20) returns False (WRONG!)
''',
    'expected_fix': '''def is_adult(age):
    """Check if person is adult (18+).
    
    Args:
        age: Person's age
    
    Returns:
        bool: True if 18 or older, False otherwise
    """
    return age >= 18
'''
}

# ============================================================================
# ERROR 4: Typo in variable name
# ============================================================================
dataset_logic_4 = {
    'name': 'Variable name typo causes wrong calculation',
    'file': 'logic_error_4.py',
    'code': '''def greet_user(first_name, last_name):
    # WRONG: Uses greating instead of greeting
    greating = f"Hello, {first_name} {last_name}"
    return greeting  # KeyError! Variable greating was never defined

# Expected: greet_user("John", "Doe") returns "Hello, John Doe"
# Actual: NameError: name 'greeting' is not defined
''',
    'expected_fix': '''def greet_user(first_name, last_name):
    """Generate greeting message.
    
    Args:
        first_name: Person's first name
        last_name: Person's last name
    
    Returns:
        str: Greeting message
    """
    greeting = f"Hello, {first_name} {last_name}"
    return greeting
'''
}

# ============================================================================
# ERROR 5: Incorrect type conversion
# ============================================================================
dataset_logic_5 = {
    'name': 'Wrong type in calculation',
    'file': 'logic_error_5.py',
    'code': '''def calculate_average(numbers):
    # WRONG: Divides by list instead of length
    total = sum(numbers)
    return total / numbers  # TypeError!

# Expected: calculate_average([10, 20, 30]) returns 20.0
# Actual: TypeError: unsupported operand type(s) for /: 'int' and 'list'
''',
    'expected_fix': '''def calculate_average(numbers):
    """Calculate average of numbers.
    
    Args:
        numbers: List of numbers
    
    Returns:
        float: Average value
    
    Raises:
        ValueError: If list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
'''
}


LOGIC_ERROR_DATASETS = [
    dataset_logic_1,
    dataset_logic_2,
    dataset_logic_3,
    dataset_logic_4,
    dataset_logic_5
]
