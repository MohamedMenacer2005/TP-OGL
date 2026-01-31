def greet_user(first_name, last_name):
    # WRONG: Uses greating instead of greeting
    greating = f"Hello, {first_name} {last_name}"
    return greeting  # KeyError! Variable greating was never defined

# Expected: greet_user("John", "Doe") returns "Hello, John Doe"
# Actual: NameError: name 'greeting' is not defined
