def get_first_n_items(items, n):
    result = []
    for i in range(n):
        if i < len(items):
            result.append(items[i])
    return result

# Test:
# items = [1, 2, 3, 4, 5]
# get_first_n_items(items, 3) should return [1, 2, 3]
# But returns [1, 2, 3] correctly in this case
