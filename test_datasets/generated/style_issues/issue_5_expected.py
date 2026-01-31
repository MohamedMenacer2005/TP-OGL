def load_config(filepath):
    try:
        with open(filepath) as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading config: {e}")
        return None
