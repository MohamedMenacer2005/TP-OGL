def calculate_average(numbers):
    # WRONG: Divides by list instead of length
    total = sum(numbers)
    return total / numbers  # TypeError!

# Expected: calculate_average([10, 20, 30]) returns 20.0
# Actual: TypeError: unsupported operand type(s) for /: 'int' and 'list'
