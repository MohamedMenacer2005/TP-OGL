import json
with open('logs/experiment_data.json') as f:
    data = json.load(f)
tests = [e for e in data if 'passed' in str(e.get('details', {}))]
print(f'Entries with test results: {len(tests)}')
for e in tests[-2:]:
    print(f"  passed={e['details'].get('passed')}, failed={e['details'].get('failed')}")
