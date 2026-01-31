"""
TEST DATASET: STYLE & QUALITY ISSUES
=====================================
Collection de fichiers avec des problèmes de style et qualité (détectables par pylint).
"""

# ============================================================================
# ISSUE 1: Unused imports
# ============================================================================
dataset_style_1 = {
    'name': 'Unused imports',
    'file': 'style_issue_1.py',
    'code': '''import os
import sys  # Unused
from pathlib import Path  # Unused

def get_home():
    return os.path.expanduser("~")
''',
    'expected_fix': '''import os

def get_home():
    return os.path.expanduser("~")
'''
}

# ============================================================================
# ISSUE 2: Non-standard naming
# ============================================================================
dataset_style_2 = {
    'name': 'Non-standard variable naming (snake_case)',
    'file': 'style_issue_2.py',
    'code': '''def calculate_total():
    itemPrice = 10  # Should be item_price
    totalItems = 5  # Should be total_items
    return itemPrice * totalItems
''',
    'expected_fix': '''def calculate_total():
    item_price = 10
    total_items = 5
    return item_price * total_items
'''
}

# ============================================================================
# ISSUE 3: Too many statements in function
# ============================================================================
dataset_style_3 = {
    'name': 'Function with low cohesion (missing docstring)',
    'file': 'style_issue_3.py',
    'code': '''def process_payment(amount, user_id, account):
    if amount <= 0:
        return False
    if user_id is None:
        return False
    if account.balance < amount:
        return False
    account.balance -= amount
    return True
''',
    'expected_fix': '''def process_payment(amount, user_id, account):
    """Process payment transaction.
    
    Args:
        amount: Transaction amount
        user_id: User identifier
        account: Account object
    
    Returns:
        bool: True if payment successful, False otherwise
    """
    if amount <= 0:
        return False
    if user_id is None:
        return False
    if account.balance < amount:
        return False
    account.balance -= amount
    return True
'''
}

# ============================================================================
# ISSUE 4: Bad line length
# ============================================================================
dataset_style_4 = {
    'name': 'Line too long',
    'file': 'style_issue_4.py',
    'code': '''def send_notification(user_id, message, timestamp, channel, priority):
    notification_payload = {"user_id": user_id, "message": message, "timestamp": timestamp, "channel": channel, "priority": priority}
    return notification_payload
''',
    'expected_fix': '''def send_notification(user_id, message, timestamp, channel, priority):
    notification_payload = {
        "user_id": user_id,
        "message": message,
        "timestamp": timestamp,
        "channel": channel,
        "priority": priority
    }
    return notification_payload
'''
}

# ============================================================================
# ISSUE 5: Bare except clause
# ============================================================================
dataset_style_5 = {
    'name': 'Bare except clause (catches everything)',
    'file': 'style_issue_5.py',
    'code': '''def load_config(filepath):
    try:
        with open(filepath) as f:
            return f.read()
    except:  # BAD: Should specify exception type
        return None
''',
    'expected_fix': '''def load_config(filepath):
    try:
        with open(filepath) as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading config: {e}")
        return None
'''
}


STYLE_ISSUE_DATASETS = [
    dataset_style_1,
    dataset_style_2,
    dataset_style_3,
    dataset_style_4,
    dataset_style_5
]
