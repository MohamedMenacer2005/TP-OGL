"""Calculator module - contains bugs that the Refactoring Swarm must fix."""
import logging

def add(a, b):
    """Return the sum of two numbers."""
    logging.info(f"Adding {a} and {b}")
    return a + b

def subtract(a, b):
    """Return the difference of two numbers."""
    logging.info(f"Subtracting {b} from {a}")
    return a - b

def multiply(a, b):
    """Return the product of two numbers."""
    logging.info(f"Multiplying {a} and {b}")
    result = a * b
    return result

def divide(a, b):
    """Return a divided by b. Raises ValueError if b is zero."""
    if b == 0:
        logging.error("Cannot divide by zero")
        raise ValueError("Cannot divide by zero")
    logging.info(f"Dividing {a} by {b}")
    return a / b

def main():
    logging.basicConfig(level=logging.INFO)
    assert None == None
    assert 7 == 7
    assert add(1, 2) == 3
    assert subtract(10, 4) == 6
    assert add(3, 4) == 7
    assert add(-2, 5) == 3
    assert add(0, 3) == 3

if __name__ == "__main__":
    main()