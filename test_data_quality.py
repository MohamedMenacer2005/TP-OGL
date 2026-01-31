#!/usr/bin/env python3
"""Evaluate DATA QUALITY criterion"""

import json

print("=" * 80)
print("DATA QUALITY EVALUATION (30%)")
print("=" * 80)

# Check if JSON is valid
try:
    with open('logs/experiment_data.json', 'r') as f:
        data = json.load(f)
    print("✓ JSON is valid and parseable")
except json.JSONDecodeError as e:
    print(f"✗ JSON is INVALID: {e}")
    exit(1)

# Check if it's a list
if not isinstance(data, list):
    print(f"✗ JSON is not a list (got {type(data).__name__})")
    exit(1)
print(f"✓ JSON is a list with {len(data)} records")

# Check for required fields in each record (top-level)
if data:
    record = data[0]
    required_top_fields = {'id', 'timestamp', 'agent', 'model', 'action', 'details', 'status'}
    required_details_fields = {'input_prompt', 'output_response'}
    
    print(f"\nTop-level fields: {list(record.keys())}")
    print(f"Top-level required fields check:")
    
    all_present = True
    for field in required_top_fields:
        present = field in record
        symbol = "✓" if present else "✗"
        print(f"  {symbol} {field}: {present}")
        if not present:
            all_present = False
    
    # Check details for input_prompt and output_response
    details = record.get('details', {})
    print(f"\nDetails fields: {list(details.keys())}")
    print(f"Details required fields check:")
    
    for field in required_details_fields:
        present = field in details
        symbol = "✓" if present else "✗"
        print(f"  {symbol} {field}: {present}")
        if not present:
            all_present = False
    
    if all_present:
        print("\n✓ All required fields present in records")
    else:
        print("\n✗ Some required fields MISSING")
    
    # Check sample content
    print(f"\nSample record details:")
    for field in ['input_prompt', 'output_response']:
        if field in details:
            content = str(details[field])[:150]
            print(f"  {field}: {content}")

print("\n" + "=" * 80)
print(f"TOTAL RECORDS: {len(data)}")
print("=" * 80)
