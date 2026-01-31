import json

data = json.load(open('logs/experiment_data.json'))

# Vérifier les corrections appliquées
fixes = [e for e in data if e['action'] == 'FIX']
print(f"Total corrections appliquées: {len(fixes)}\n")

if fixes:
    print("Détails des corrections:")
    for fix in fixes:
        filename = fix['details'].get('filename', 'unknown')
        status = fix['status']
        agent = fix['agent']
        print(f"  [{agent}] {filename}: {status}")
        if 'output_response' in fix['details']:
            resp = fix['details']['output_response'][:100]
            print(f"       Response: {resp}...")
else:
    print("❌ Aucune correction trouvée!")

# Vérifier les analyses
print("\n" + "="*50)
analyses = [e for e in data if e['action'] == 'CODE_ANALYSIS']
print(f"Total analyses: {len(analyses)}")
