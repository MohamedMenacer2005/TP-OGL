def calculate_price_with_tax(base_price, tax_rate):
    # WRONG: Multiplies by tax_rate instead of (1 + tax_rate)
    return base_price * tax_rate

# Expected: 100 with 0.2 tax rate should be 120
# Actual: 100 * 0.2 = 20 (WRONG!)
