def is_adult(age):
    # WRONG: Uses == instead of >=
    return age == 18  # Only returns True for exactly 18

# Expected: is_adult(20) should be True
# Actual: is_adult(20) returns False (WRONG!)
