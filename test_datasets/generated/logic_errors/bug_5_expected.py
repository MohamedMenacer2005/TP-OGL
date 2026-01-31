def calculate_average(numbers):
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
