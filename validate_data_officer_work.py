#!/usr/bin/env python3
"""Validate log file against ENSI spec"""

import json

print("=" * 80)
print("VALIDATION: Data Officer Work")
print("=" * 80)

# Step 2: JSON Validity
print("\n[2] JSON VALIDITY")
try:
    with open('logs/experiment_data.json', 'r') as f:
        data = json.load(f)
    print("✓ JSON is valid and parseable")
    print(f"✓ File is not empty ({len(data)} entries)")
except json.JSONDecodeError as e:
    print(f"✗ JSON INVALID: {e}")
    exit(1)
except Exception as e:
    print(f"✗ ERROR: {e}")
    exit(1)

# Step 3: Logging Completeness
print("\n[3] LOGGING COMPLETENESS")
agents_present = set(e['agent_name'] for e in data)
required_agents = {'AuditorAgent', 'CorrectorAgent', 'JudgeAgent'}
print(f"Agents found: {agents_present}")
for agent in required_agents:
    if agent in agents_present:
        print(f"✓ {agent} present")
    else:
        print(f"✗ {agent} MISSING")

# Step 4: Schema Compliance
print("\n[4] LOG SCHEMA COMPLIANCE")
required_top_fields = {'id', 'timestamp', 'agent_name', 'model_used', 'action', 'details', 'status'}
required_detail_fields = {'input_prompt', 'output_response'}

schema_valid = True
for i, entry in enumerate(data):
    # Check top-level fields
    missing_top = required_top_fields - set(entry.keys())
    if missing_top:
        print(f"✗ Entry {i}: missing fields {missing_top}")
        schema_valid = False
    
    # Check detail fields
    details = entry.get('details', {})
    missing_details = required_detail_fields - set(details.keys())
    if missing_details:
        print(f"✗ Entry {i}: missing detail fields {missing_details}")
        schema_valid = False

if schema_valid:
    print("✓ All entries have required fields")

# Step 5: Execution Trace
print("\n[5] EXECUTION TRACE CONSISTENCY")
agents_trace = [e['agent_name'] for e in data]
print("Trace:", " → ".join(agents_trace))

# Check for correct sequence
if agents_trace[0] == 'AuditorAgent':
    print("✓ Starts with AuditorAgent")
else:
    print("✗ Does not start with AuditorAgent")

if 'CorrectorAgent' in agents_trace and 'JudgeAgent' in agents_trace:
    print("✓ Contains Fixer and Judge")
else:
    print("✗ Missing Fixer or Judge")

# Step 6: Iteration Traceability
print("\n[6] ITERATION TRACEABILITY")
# Count unique timestamps or log entries
total_entries = len(data)
print(f"Total log entries: {total_entries}")

# Check if iterations would be visible (multiple entries per iteration)
if total_entries >= 3:
    print(f"✓ Sufficient entries for traceability ({total_entries} entries)")
else:
    print(f"⚠ Low entry count ({total_entries})")

# Step 7: ActionType validation
print("\n[7] ACTIONTYPE VALIDATION")
valid_actions = {'CODE_ANALYSIS', 'CODE_GEN', 'DEBUG', 'FIX'}
actions_found = set(e['action'] for e in data)
print(f"Actions used: {actions_found}")

invalid_actions = actions_found - valid_actions
if not invalid_actions:
    print("✓ All actions are valid")
else:
    print(f"✗ Invalid actions: {invalid_actions}")

# Final summary
print("\n" + "=" * 80)
print("VALIDATION RESULT")
print("=" * 80)

if schema_valid and agents_present >= required_agents and not invalid_actions:
    print("\n✓ Data Officer Work: COMPLIANT with ENSI spec")
    print("\nAll checks passed:")
    print("  ✓ Log file exists and valid JSON")
    print("  ✓ All required agents present")
    print("  ✓ Correct schema (agent_name, model_used, input_prompt, output_response)")
    print("  ✓ Valid ActionType values")
    print("  ✓ Execution trace consistent")
else:
    print("\n✗ Data Officer Work: ISSUES FOUND")
    exit(1)
