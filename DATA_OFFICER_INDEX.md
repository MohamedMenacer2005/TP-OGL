# 📊 DATA OFFICER - Index des Fichiers

## Structure créée pour le rôle "Responsable Qualité & Data"

### 🎯 Fichiers Principaux

| Fichier | Rôle | Utilisation |
|---------|------|-------------|
| [src/data_officer.py](src/data_officer.py) | **Module central** | `from src.data_officer import DataOfficer` |
| [verify_before_submission.py](verify_before_submission.py) | **Checklist ENSI** | `python verify_before_submission.py` |
| [DATA_OFFICER.md](DATA_OFFICER.md) | **Documentation** | Guide complet avec exemples |
| [data_officer_summary.py](data_officer_summary.py) | **Résumé** | `python data_officer_summary.py` |

### 🧪 Jeux de Données de Test

| Répertoire | Contenu | Fichiers |
|------------|---------|----------|
| [test_datasets/syntax_errors.py](test_datasets/syntax_errors.py) | 5 erreurs de syntaxe définies | `SYNTAX_ERROR_DATASETS` |
| [test_datasets/style_issues.py](test_datasets/style_issues.py) | 5 problèmes de style définis | `STYLE_ISSUE_DATASETS` |
| [test_datasets/logic_errors.py](test_datasets/logic_errors.py) | 5 erreurs logiques définies | `LOGIC_ERROR_DATASETS` |
| [test_datasets_generator.py](test_datasets_generator.py) | **Générateur** | `python test_datasets_generator.py` |
| [test_datasets/generated/](test_datasets/generated/) | **Fichiers générés** | 15 fichiers Python + manifests |

### 📋 Checklist Pré-Soumission

**10 Tests automatisés** dans [verify_before_submission.py](verify_before_submission.py) :

```
[TEST 1-3]   ROBUSTESSE TECHNIQUE (30%)
[TEST 4-6]   QUALITÉ DES DONNÉES (30%)
[TEST 7-9]   PERFORMANCE (40%)
[TEST 10]    ENVIRONNEMENT
```

---

## 🚀 Commandes Rapides

### Générer les datasets

```bash
python test_datasets_generator.py
```

Crée 15 fichiers Python dans `test_datasets/generated/` avec :
- 5 erreurs de syntaxe (error_1.py à error_5.py)
- 5 problèmes de style (issue_1.py à issue_5.py)
- 5 erreurs logiques (bug_1.py à bug_5.py)
- Chaque fichier a une version "expected" avec le code corrigé

### Vérifier avant soumission

```bash
python verify_before_submission.py
```

Lance 10 vérifications ENSI avec rapport d'intégrité détaillé.

### Rapport Data Officer

```bash
python data_officer_summary.py
python -c "from src.data_officer import print_data_officer_report; print_data_officer_report()"
```

Affiche le statut de conformité ENSI.

### Exécuter avec Data Officer intégré

```bash
python main.py --target_dir ./sandbox
```

Automatiquement :
- ✅ Pre-flight check avant démarrage
- ✅ Post-flight validation à la fin avec rapport complet

---

## 📊 Structure des Données

### Schéma ENSI imposé

Chaque entrée dans `logs/experiment_data.json` doit avoir :

```json
{
  "id": "uuid-unique-pour-chaque-execution",
  "timestamp": "2026-01-31T12:34:56.789123",
  "agent_name": "AuditorAgent",
  "model_used": "models/gemini-2.5-flash",
  "action": "CODE_ANALYSIS",
  "details": {
    "input_prompt": "Exact prompt sent to LLM",
    "output_response": "Full LLM response received",
    "optional_field": "Any additional context"
  },
  "status": "SUCCESS"
}
```

**⚠️ Obligatoire** : `input_prompt` et `output_response` dans `details`

---

## ✅ Conformité ENSI - 3 Critères

### 1. Robustesse Technique (30%)

- ✅ Système stable (pas de crash)
- ✅ Respect du paramètre `--target_dir`
- ✅ Limite de 10 itérations maximum

### 2. Qualité des Données (30%)

- ✅ Schéma ENSI 100% respecté
- ✅ Tracking complet prompt/response
- ✅ Pas de doublons
- ✅ JSON valide et complet

### 3. Performance (40%)

- ✅ Exécution des tests (pytest)
- ✅ Taux de succès des agents
- ✅ Coordination multi-agent (3+ agents)

---

## 🔍 Diagnostic

### Si `verify_before_submission.py` échoue

1. **Erreurs de schéma** → Vérifier `src/utils/logger.py`
2. **Prompts manquants** → Vérifier que tous les agents enregistrent avec `input_prompt` et `output_response`
3. **Fichiers manquants** → Vérifier la structure du répertoire

### Générer diagnostic complet

```python
from src.data_officer import DataOfficer

officer = DataOfficer()
print(officer.generate_report())
```

---

## 📚 Documentation

Pour la documentation complète, voir [DATA_OFFICER.md](DATA_OFFICER.md) avec :
- Exemples d'utilisation
- API complète de DataOfficer
- Structure des datasets
- Troubleshooting

---

## 📌 Fichiers modifiés

| Fichier | Changements |
|---------|-------------|
| [main.py](main.py) | +Data Officer pre-flight et post-flight checks |

---

**Créé par** : Data Officer Module  
**Date** : 2026-01-31  
**Conformité** : ENSI TP IGL 2025-2026 - Responsable Qualité & Télémétrie
