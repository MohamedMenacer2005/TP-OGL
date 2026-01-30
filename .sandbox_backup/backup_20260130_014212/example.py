"""
Test file for Phase 1
A simple Python file with some code quality issues.
"""


def greet(name):
    # Missing type hints
    return "Hello, " + name


class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, x, y):
        # Could use type hints
        self.result = x + y
        return self.result
    
    def unused_method(self):
        # This method is never called
        pass
