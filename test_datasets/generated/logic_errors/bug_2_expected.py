def calculate_price_with_tax(base_price, tax_rate):
    """Calculate price with tax applied.
    
    Args:
        base_price: Original price
        tax_rate: Tax rate (e.g., 0.2 for 20%)
    
    Returns:
        float: Price with tax applied
    """
    return base_price * (1 + tax_rate)
