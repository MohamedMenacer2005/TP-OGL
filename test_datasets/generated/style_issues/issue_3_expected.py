def process_payment(amount, user_id, account):
    """Process payment transaction.
    
    Args:
        amount: Transaction amount
        user_id: User identifier
        account: Account object
    
    Returns:
        bool: True if payment successful, False otherwise
    """
    if amount <= 0:
        return False
    if user_id is None:
        return False
    if account.balance < amount:
        return False
    account.balance -= amount
    return True
