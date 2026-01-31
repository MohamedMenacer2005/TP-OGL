#!/usr/bin/env python3
"""
DATA OFFICER MODULE
==================
Responsable de la télémétrie et de la qualité des données.
Valide que chaque action des agents est enregistrée correctement selon le schéma ENSI.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from collections import defaultdict

LOG_FILE = Path("logs/experiment_data.json")

class DataOfficer:
    """Gestionnaire de qualité des données et télémétrie."""
    
    # Schéma ENSI imposé
    REQUIRED_TOP_FIELDS = {
        'id', 'timestamp', 'agent_name', 'model_used', 'action', 'details', 'status'
    }
    
    REQUIRED_DETAILS_FIELDS = {
        'input_prompt', 'output_response'
    }
    
    VALID_ACTIONS = {
        'CODE_ANALYSIS', 'CODE_GEN', 'DEBUG', 'FIX'
    }
    
    VALID_STATUSES = {'SUCCESS', 'FAILURE'}
    
    def __init__(self):
        self.logs = []
        self.validation_issues = []
        self.warnings = []
        self.load_logs()
    
    def load_logs(self) -> bool:
        """Charge les logs depuis experiment_data.json."""
        if not LOG_FILE.exists():
            self.warnings.append("⚠️ Fichier de logs n'existe pas encore")
            return False
        
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                self.logs = json.load(f)
            return True
        except json.JSONDecodeError as e:
            self.validation_issues.append(f"❌ JSON CORROMPU: {e}")
            return False
        except Exception as e:
            self.validation_issues.append(f"❌ Erreur de lecture: {e}")
            return False
    
    def validate_schema(self) -> bool:
        """
        Valide que tous les logs respectent le schéma ENSI.
        Retourne True si 100% conformité, False sinon.
        """
        all_valid = True
        
        for idx, entry in enumerate(self.logs):
            # Vérifier champs top-level
            missing_fields = self.REQUIRED_TOP_FIELDS - set(entry.keys())
            if missing_fields:
                self.validation_issues.append(
                    f"❌ Entrée {idx}: Champs manquants {missing_fields}"
                )
                all_valid = False
            
            # Vérifier action valide
            action = entry.get('action')
            if action not in self.VALID_ACTIONS:
                self.validation_issues.append(
                    f"❌ Entrée {idx}: Action invalide '{action}' (acceptées: {self.VALID_ACTIONS})"
                )
                all_valid = False
            
            # Vérifier statut valide
            status = entry.get('status')
            if status not in self.VALID_STATUSES:
                self.validation_issues.append(
                    f"❌ Entrée {idx}: Statut invalide '{status}' (acceptés: {self.VALID_STATUSES})"
                )
                all_valid = False
            
            # Vérifier champs details
            details = entry.get('details', {})
            missing_details = self.REQUIRED_DETAILS_FIELDS - set(details.keys())
            if missing_details:
                self.validation_issues.append(
                    f"❌ Entrée {idx}: 'details' manque {missing_details}"
                )
                all_valid = False
            
            # Vérifier que prompt/response ne sont pas vides
            input_prompt = details.get('input_prompt', '')
            output_response = details.get('output_response', '')
            
            if input_prompt and len(str(input_prompt).strip()) < 10:
                self.warnings.append(
                    f"⚠️ Entrée {idx}: input_prompt très court ({len(input_prompt)} chars)"
                )
            
            if output_response and len(str(output_response).strip()) < 5:
                self.warnings.append(
                    f"⚠️ Entrée {idx}: output_response très court ({len(output_response)} chars)"
                )
        
        return all_valid
    
    def detect_duplicates(self) -> List[str]:
        """Détecte les entrées dupliquées par agent+action+timestamp."""
        duplicates = []
        seen = defaultdict(list)
        
        for idx, entry in enumerate(self.logs):
            key = (
                entry.get('agent_name'),
                entry.get('action'),
                entry.get('timestamp')[:16]  # Grouper par minute
            )
            seen[key].append(idx)
        
        for key, indices in seen.items():
            if len(indices) > 1:
                duplicates.append(
                    f"⚠️ Logs potentiellement dupliqués: "
                    f"Agent={key[0]}, Action={key[1]}, Time={key[2]} (indices: {indices})"
                )
        
        return duplicates
    
    def get_statistics(self) -> Dict:
        """Calcule les statistiques d'exécution."""
        stats = {
            'total_entries': len(self.logs),
            'success_rate': 0.0,
            'agents': defaultdict(int),
            'models': defaultdict(int),
            'actions': defaultdict(int),
            'status_distribution': defaultdict(int)
        }
        
        if not self.logs:
            return stats
        
        success_count = 0
        
        for entry in self.logs:
            agent = entry.get('agent_name', 'UNKNOWN')
            model = entry.get('model_used', 'UNKNOWN')
            action = entry.get('action', 'UNKNOWN')
            status = entry.get('status', 'UNKNOWN')
            
            stats['agents'][agent] += 1
            stats['models'][model] += 1
            stats['actions'][action] += 1
            stats['status_distribution'][status] += 1
            
            if status == 'SUCCESS':
                success_count += 1
        
        stats['success_rate'] = (success_count / len(self.logs)) * 100 if self.logs else 0
        
        return stats
    
    def generate_report(self) -> str:
        """Génère un rapport de conformité ENSI."""
        report = []
        report.append("\n" + "=" * 80)
        report.append("RAPPORT DATA OFFICER - CONFORMITÉ ENSI")
        report.append("=" * 80)
        
        # Section 1: Existence du fichier
        report.append("\n[1] PRÉSENCE DU FICHIER DE LOGS")
        if LOG_FILE.exists():
            size = LOG_FILE.stat().st_size
            report.append(f"✅ logs/experiment_data.json existe ({size} bytes)")
        else:
            report.append("❌ logs/experiment_data.json ABSENT")
            return "\n".join(report)
        
        # Section 2: Validité du schéma
        report.append("\n[2] VALIDATION DU SCHÉMA ENSI")
        schema_valid = self.validate_schema()
        if schema_valid:
            report.append("✅ Schéma VALIDE - 100% conformité")
        else:
            report.append(f"❌ {len(self.validation_issues)} erreurs détectées:")
            for issue in self.validation_issues[:10]:
                report.append(f"   {issue}")
            if len(self.validation_issues) > 10:
                report.append(f"   ... et {len(self.validation_issues) - 10} autres")
        
        # Section 3: Doublons
        report.append("\n[3] DÉTECTION DE DOUBLONS")
        duplicates = self.detect_duplicates()
        if not duplicates:
            report.append("✅ Aucun doublon détecté")
        else:
            report.append(f"⚠️  {len(duplicates)} potentiels doublons:")
            for dup in duplicates[:5]:
                report.append(f"   {dup}")
        
        # Section 4: Statistiques
        report.append("\n[4] STATISTIQUES")
        stats = self.get_statistics()
        report.append(f"✅ Total entrées: {stats['total_entries']}")
        report.append(f"✅ Taux de succès: {stats['success_rate']:.1f}%")
        report.append(f"✅ Agents actifs: {len(stats['agents'])}")
        for agent, count in sorted(stats['agents'].items()):
            report.append(f"   - {agent}: {count} opérations")
        report.append(f"✅ Modèles utilisés: {len(stats['models'])}")
        for model, count in sorted(stats['models'].items()):
            report.append(f"   - {model}: {count} opérations")
        
        # Section 5: Distribution des actions
        report.append("\n[5] DISTRIBUTION DES ACTIONS")
        for action, count in sorted(stats['actions'].items()):
            report.append(f"   - {action}: {count}")
        
        # Section 6: Avertissements
        if self.warnings:
            report.append("\n[6] AVERTISSEMENTS")
            for warning in self.warnings[:5]:
                report.append(f"   {warning}")
            if len(self.warnings) > 5:
                report.append(f"   ... et {len(self.warnings) - 5} autres")
        
        # Section 7: Conformité finale
        report.append("\n[7] STATUT FINAL")
        if schema_valid and stats['success_rate'] == 100 and not duplicates:
            report.append("✅ ✅ ✅ CONFORME AUX SPÉCIFICATIONS ENSI ✅ ✅ ✅")
        elif schema_valid and stats['success_rate'] >= 95:
            report.append("⚠️  GLOBALEMENT CONFORME (quelques avertissements mineurs)")
        else:
            report.append("❌ NON CONFORME - Corrections requises")
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)
    
    def verify_data_integrity(self) -> Tuple[bool, str]:
        """
        Vérification complète d'intégrité des données.
        Retourne (is_valid, message).
        """
        if not LOG_FILE.exists():
            return False, "❌ Fichier de logs n'existe pas"
        
        if not self.logs:
            return False, "❌ Fichier de logs est vide"
        
        all_issues = self.validation_issues + self.warnings
        if all_issues:
            return False, f"❌ {len(all_issues)} problèmes détectés"
        
        stats = self.get_statistics()
        if stats['success_rate'] < 100:
            return False, f"⚠️  Taux de succès: {stats['success_rate']:.1f}%"
        
        return True, "✅ Intégrité des données VALIDÉE"


def print_data_officer_report():
    """Affiche le rapport Data Officer."""
    officer = DataOfficer()
    print(officer.generate_report())
    return officer


if __name__ == "__main__":
    print_data_officer_report()
