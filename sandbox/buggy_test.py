"""
Buggy Python Code for Testing Refactoring Agents
Contains intentional bugs for testing purposes
"""


def calculate_total_with_tax(price):
    """Calculate total price with tax (BUGGY: undefined tax_rate)"""
    return price + (price * tax_rate)  # BUG: tax_rate not defined


def greet_user(name):
    """Greet a user (BUGGY: typo in variable name)"""
    return f"Hello, {nam}!"  # BUG: should be 'name' not 'nam'


def process_order(items):
    """Process an order (BUGGY: doesn't return anything)"""
    total = 0
    for item in items:
        total += item['price']
    # BUG: missing return statement


class BankAccount:
    """Bank account class (BUGGY: __init__ signature mismatch)"""
    
    def __init__(self, owner):  # BUG: tests expect (owner, balance) but this only takes owner
        self.owner = owner
        self.balance = 0
    
    def deposit(self, amount):
        """Deposit money"""
        if amount > 0:
            self.balance += amount
            return True
        return False
    
    def withdraw(self, amount):
        """Withdraw money"""
        if amount > 0 and amount <= self.balance:
            self.balance -= amount
            return True
        return False
    
    def get_balance(self):
        """Get current balance"""
        return self.balance


def read_file_unsafe(filename):
    """Read file without error handling"""
    with open(filename, 'r') as f:  # BUG: no try/except
        return f.read()


def parse_json_unsafe(json_string):
    """Parse JSON without validation"""
    import json
    return json.loads(json_string)  # BUG: no error handling


def divide_unsafe(a, b):
    """Divide two numbers"""
    return a / b  # BUG: no check for division by zero
