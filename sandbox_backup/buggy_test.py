"""
Buggy Python Code for Testing Refactoring Agents
Contains intentional bugs for testing purposes
"""


def calculate_total_with_tax(price, tax_rate=0.1):
    """Calculate total price with tax (BUGGY: undefined tax_rate)"""
    return price + (price * tax_rate)  # BUG: tax_rate not defined


def greet_user(name):
    """Greet a user (BUGGY: typo in variable name)"""
    return f"Hello, {name}!"  # BUG: should be 'name' not 'nam'


def process_order(items):
    """Process an order (BUGGY: doesn't return anything)"""
    total = 0
    for item in items:
        total += item['price']
    return total
    # BUG: missing return statement


class BankAccount:
    """Bank account class (BUGGY: __init__ signature mismatch)"""
    
    def __init__(self, owner, balance=0):  # BUG: tests expect (owner, balance) but this only takes owner
        self.owner = owner
        self.balance = balance
    
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
    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None


def parse_json_unsafe(json_string):
    """Parse JSON without validation"""
    import json
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, ValueError):
        return None  # BUG: no error handling


def divide_unsafe(a, b):
    """Divide two numbers"""
    if b == 0:
        raise ValueError('Cannot divide by zero')
    return a / b  # BUG: no check for division by zero

class Calculator:
    # Missing docstring
    def __init__(self):
        pass
    
    def calculate(self,operation,a,b):
        # Missing docstring, no input validation, poor spacing
        if operation=="add":
            return a+b
        elif operation=="subtract":
            return a-b
        elif operation=="multiply":
            return a*b
        elif operation=="divide":
            return a/b
        else:
            return None

# Unused import
import sys
import os

# Dead code
def unused_function():
    x = 5
    y = 10
    z = x + y
    # Function does nothing useful