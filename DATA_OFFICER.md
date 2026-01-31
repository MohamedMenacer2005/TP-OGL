# 📊 DATA OFFICER - Module de Qualité & Télémétrie

## Vue d'ensemble

Le **Data Officer** est le responsable de la télémétrie et de la qualité des données dans le système multi-agent TP-OGL. Il garantit que :

1. ✅ **Chaque action des agents est enregistrée** dans `logs/experiment_data.json`
2. ✅ **Le schéma ENSI est strictement respecté** (champs obligatoires, formats)
3. ✅ **Les données scientifiques sont intègres** (pas de doublons, complétude)
4. ✅ **Un jeu de données de test interne valide** le système avant soumission

---

## 📁 Structure créée

### 1. Module Data Officer : `src/data_officer.py`

**Classe principale** : `DataOfficer`

#### Méthodes clés

```python
# Charger les logs
officer = DataOfficer()

# Valider le schéma ENSI (100% conformité)
is_valid = officer.validate_schema()

# Détecter les doublons
duplicates = officer.detect_duplicates()

# Statistiques d'exécution
stats = officer.get_statistics()
# Retourne: total_entries, success_rate, agents, models, actions, status_distribution

# Générer rapport ENSI complet
report = officer.generate_report()
print(report)

# Vérifier intégrité (retour booléen + message)
is_ok, msg = officer.verify_data_integrity()
```

#### Schéma ENSI validé

```python
# Structure obligatoire pour chaque log
{
    "id": "uuid",                              # Unique per entry
    "timestamp": "2026-01-31T12:00:00",       # ISO format
    "agent_name": "AuditorAgent",             # Exact name
    "model_used": "models/gemini-2.5-flash",  # Model identifier
    "action": "CODE_ANALYSIS",                # Enum: CODE_ANALYSIS|CODE_GEN|DEBUG|FIX
    "details": {
        "input_prompt": "...",                # MANDATORY - exact prompt sent to LLM
        "output_response": "...",             # MANDATORY - full LLM response
        # Optional custom fields allowed
    },
    "status": "SUCCESS"                       # SUCCESS or FAILURE
}
```

---

### 2. Jeux de Données de Test : `test_datasets/`

**3 catégories de problèmes Python** : 15 fichiers de test

#### Structure

```
test_datasets/
├── syntax_errors.py          # Définitions des erreurs de syntaxe
├── style_issues.py           # Définitions des problèmes de style
├── logic_errors.py           # Définitions des erreurs logiques
└── generated/
    ├── manifest.json
    ├── syntax_errors/
    │   ├── error_1.py
    │   ├── error_1_expected.py
    │   └── index.json
    ├── style_issues/
    │   ├── issue_1.py
    │   ├── issue_1_expected.py
    │   └── index.json
    └── logic_errors/
        ├── bug_1.py
        ├── bug_1_expected.py
        └── index.json
```

#### Catégories

| Catégorie | Nombre | Détails |
|-----------|--------|---------|
| **Syntax Errors** | 5 | Manque `:`, indentation, chaîne non fermée, parenthèse manquante, opérateur invalide |
| **Style Issues** | 5 | Imports inutiles, nommage non-standard, docstrings manquantes, lignes trop longues, bare except |
| **Logic Errors** | 5 | Off-by-one, calcul de taxe incorrect, mauvaise comparaison, typo variable, conversion de type |

#### Utilisation

```python
from test_datasets.syntax_errors import SYNTAX_ERROR_DATASETS
from test_datasets.style_issues import STYLE_ISSUE_DATASETS
from test_datasets.logic_errors import LOGIC_ERROR_DATASETS

# Chaque dataset a cette structure
dataset = SYNTAX_ERROR_DATASETS[0]
print(dataset['name'])              # Human-readable description
print(dataset['code'])              # Code with bug
print(dataset['expected_fix'])       # Expected corrected code
```

#### Générer les fichiers de test

```bash
python test_datasets_generator.py
# Crée: test_datasets/generated/
```

---

### 3. Script de Vérification Pré-Soumission : `verify_before_submission.py`

**Checklist complète ENSI** : 10 tests automatisés

#### Utilisation

```bash
python verify_before_submission.py
```

#### Critères vérifiés

| Critère | Poids | Tests |
|---------|-------|-------|
| **Robustesse Technique** | 30% | Stabilité système, --target_dir, limite 10 itérations |
| **Qualité des Données** | 30% | Schéma ENSI, tracking prompt/response, doublons |
| **Performance** | 40% | Test execution, taux de succès, coordination multi-agent |

#### Exemple de rapport

```
================================================================================
VERIFICATION PRE-SUBMISSION - CHECKLIST ENSI
================================================================================

[TEST 1] ROBUSTESSE TECHNIQUE - Stabilité système
  ✅ PASS: Système présent et accessible

[TEST 2] ROBUSTESSE TECHNIQUE - Paramètre --target_dir
  ✅ PASS: Argument parsing détecté

...

================================================================================
RÉSUMÉ FINAL
================================================================================

✅ Checks réussis: 10
❌ Checks échoués: 0
⚠️  Avertissements: 1

📊 Taux de réussite: 100.0%

✅ ✅ ✅ PRÊT POUR SOUMISSION ✅ ✅ ✅
```

---

## 🔄 Intégration dans main.py

Le Data Officer s'intègre **automatiquement** dans `main.py` :

### Phase 1 : Pré-flight Check

```python
# Au démarrage de main.py
[DATA OFFICER] PRE-FLIGHT VALIDATION
✅ Intégrité des données VALIDÉE
```

### Phase 2 : Post-flight Report

```python
# À la fin (succès)
[DATA OFFICER] Verifying experiment telemetry...

RAPPORT DATA OFFICER - CONFORMITÉ ENSI
[1] PRÉSENCE DU FICHIER DE LOGS
  ✅ logs/experiment_data.json existe (8675 bytes)

[2] VALIDATION DU SCHÉMA ENSI
  ✅ Schéma VALIDE - 100% conformité

[3] STATISTIQUES
  ✅ Total entrées: 12
  ✅ Taux de succès: 100.0%
  ✅ Agents actifs: 3
```

---

## 📊 Utilisation directe

### Générer un rapport Data Officer

```bash
python -c "from src.data_officer import print_data_officer_report; print_data_officer_report()"
```

### Vérifier l'intégrité des données

```python
from src.data_officer import DataOfficer

officer = DataOfficer()

# Valider schéma
is_valid = officer.validate_schema()

# Statistiques
stats = officer.get_statistics()
print(f"Success rate: {stats['success_rate']:.1f}%")
print(f"Agents: {list(stats['agents'].keys())}")

# Detecter doublons
duplicates = officer.detect_duplicates()
```

---

## ✅ Checklist avant soumission

```bash
# 1. Générer et vérifier les datasets
python test_datasets_generator.py

# 2. Exécuter la verification pré-soumission
python verify_before_submission.py

# 3. Exécuter le système une fois
python main.py --target_dir ./sandbox

# 4. Vérifier le rapport Data Officer
python -c "from src.data_officer import print_data_officer_report; print_data_officer_report()"

# 5. Confirmé ✅
# Si tout est vert, vous êtes prêt pour la soumission !
```

---

## 🎯 Responsabilités du Data Officer

Selon la spec ENSI, le Data Officer assure :

| Responsabilité | Status | Details |
|---|---|---|
| **Télémétrie complète** | ✅ | Chaque action enregistrée avec prompt/response |
| **Schéma imposé** | ✅ | Validation stricte (id, timestamp, agent_name, model_used, action, details, status) |
| **Intégrité des données** | ✅ | Détection doublons, validation JSON, complétude |
| **Dataset de test** | ✅ | 15 test cases (5 syntaxe, 5 style, 5 logique) |
| **Rapport de conformité** | ✅ | Checklist ENSI avec 10 critères |

---

## 🚀 Prochaines étapes

1. **Avant chaque exécution** : `python verify_before_submission.py`
2. **Après chaque cycle** : Vérifier le rapport Data Officer
3. **À la soumission** : Tous les checks doivent être ✅
4. **En cas de problème** : `python -c "from src.data_officer import print_data_officer_report; print_data_officer_report()"` pour diagnostiquer

---

**Créé par** : Data Officer Module  
**Date** : 2026-01-31  
**Conformité** : ENSI TP IGL 2025-2026
