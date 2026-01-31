"""
TEST DATASET: SYNTAX ERRORS
============================
Collection de fichiers Python avec des erreurs de syntaxe.
"""

# ============================================================================
# ERROR 1: Missing colon in function definition
# ============================================================================
dataset_syntax_1 = {
    'name': 'Missing colon in function',
    'file': 'syntax_error_1.py',
    'code': '''def calculate_total(items)  # ERROR: Missing colon
    total = 0
    for item in items:
        total += item
    return total
''',
    'expected_fix': '''def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total
'''
}

# ============================================================================
# ERROR 2: Indentation error
# ============================================================================
dataset_syntax_2 = {
    'name': 'Indentation error in if block',
    'file': 'syntax_error_2.py',
    'code': '''def validate_user(age):
    if age >= 18:
    print("Adult")  # ERROR: Missing indentation
    else:
        print("Minor")
''',
    'expected_fix': '''def validate_user(age):
    if age >= 18:
        print("Adult")
    else:
        print("Minor")
'''
}

# ============================================================================
# ERROR 3: Unclosed string
# ============================================================================
dataset_syntax_3 = {
    'name': 'Unclosed string literal',
    'file': 'syntax_error_3.py',
    'code': '''def greet(name):
    message = f"Hello, {name"  # ERROR: Missing closing quote
    return message
''',
    'expected_fix': '''def greet(name):
    message = f"Hello, {name}"
    return message
'''
}

# ============================================================================
# ERROR 4: Missing parenthesis
# ============================================================================
dataset_syntax_4 = {
    'name': 'Missing closing parenthesis',
    'file': 'syntax_error_4.py',
    'code': '''def process_data(data):
    result = sum(data  # ERROR: Missing closing paren
    return result
''',
    'expected_fix': '''def process_data(data):
    result = sum(data)
    return result
'''
}

# ============================================================================
# ERROR 5: Invalid operator
# ============================================================================
dataset_syntax_5 = {
    'name': 'Invalid operator in expression',
    'file': 'syntax_error_5.py',
    'code': '''def compare(a, b):
    if a => b:  # ERROR: Invalid operator (should be >=)
        return True
    return False
''',
    'expected_fix': '''def compare(a, b):
    if a >= b:
        return True
    return False
'''
}


SYNTAX_ERROR_DATASETS = [
    dataset_syntax_1,
    dataset_syntax_2,
    dataset_syntax_3,
    dataset_syntax_4,
    dataset_syntax_5
]
