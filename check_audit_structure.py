import json
from src.agents.auditor_agent import AuditorAgent

auditor = AuditorAgent()
result = auditor.execute("./sandbox")
print("Audit Result Keys:", result.keys())
print("Audit Result:")
print(json.dumps({k: v for k, v in result.items() if k != 'file_results'}, indent=2))
if result.get('file_results'):
    print("\nFile Results (first file):")
    for fname in list(result['file_results'].keys())[:1]:
        print(f"  {fname}: {result['file_results'][fname].keys()}")
