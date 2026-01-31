import json
import sys

try:
    with open('logs/experiment_data.json', 'r') as f:
        data = json.load(f)
    
    print(f"✓ JSON is valid")
    print(f"✓ Total log entries: {len(data)}")
    
    if data:
        first_entry = data[0]
        print(f"✓ Keys in entries: {list(first_entry.keys())}")
        
        action_types = set(entry['action'] for entry in data)
        print(f"✓ ActionTypes used: {action_types}")
        
        # Check for required fields
        all_valid = True
        for i, entry in enumerate(data):
            required = ['id', 'timestamp', 'agent', 'model', 'action', 'details', 'status']
            for field in required:
                if field not in entry:
                    print(f"✗ Entry {i} missing field: {field}")
                    all_valid = False
            
            # Check details for input_prompt and output_response
            if entry['action'] in ['CODE_ANALYSIS', 'CODE_GEN', 'DEBUG', 'FIX']:
                details = entry.get('details', {})
                if 'input_prompt' not in details or 'output_response' not in details:
                    print(f"✗ Entry {i} missing prompt/response in details")
                    all_valid = False
        
        if all_valid:
            print(f"✓ All entries are properly formatted")
        else:
            print(f"✗ Some entries have missing fields")
            sys.exit(1)
    
    print(f"\n✓ experiment_data.json is valid and complete")
    
except json.JSONDecodeError as e:
    print(f"✗ JSON is invalid: {e}")
    sys.exit(1)
except FileNotFoundError:
    print(f"✗ experiment_data.json not found")
    sys.exit(1)
