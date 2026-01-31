def process_payment(amount, user_id, account):
    if amount <= 0:
        return False
    if user_id is None:
        return False
    if account.balance < amount:
        return False
    account.balance -= amount
    return True
