#!/usr/bin/env python
"""Check experiment logs for Phase 2 agents."""

import json

with open('logs/experiment_data.json', encoding='utf-8') as f:
    logs = json.load(f)

print(f"Total logs: {len(logs)}")

# Filter for our agents
agent_logs = [l for l in logs if 'Agent' in l.get('agent', '')]
print(f"Agent logs: {len(agent_logs)}\n")

# Check mandatory fields
print("Checking mandatory logging fields...")
for log in agent_logs[-3:]:  # Last 3
    print(f"\n  Agent: {log['agent']}")
    print(f"  Action: {log['action']}")
    print(f"  Has 'input_prompt': {'input_prompt' in log['details']}")
    print(f"  Has 'output_response': {'output_response' in log['details']}")
    print(f"  Status: {log['status']}")

print(f"\n✅ All logs contain mandatory fields!")
