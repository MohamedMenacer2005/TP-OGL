def load_config(filepath):
    try:
        with open(filepath) as f:
            return f.read()
    except:  # BAD: Should specify exception type
        return None
