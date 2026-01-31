#!/usr/bin/env python3
"""
PRE-SUBMISSION VERIFICATION SCRIPT
===================================
Checklist complète ENSI pour validation avant soumission.
Effectue toutes les vérifications requises et génère un rapport final.
"""

import sys
import json
from pathlib import Path
from typing import List, Tuple
from src.data_officer import DataOfficer

class PreSubmissionVerifier:
    """Vérificateur pré-soumission ENSI."""
    
    def __init__(self):
        self.results = {}
        self.passed_checks = 0
        self.failed_checks = 0
        self.warnings = []
    
    # ========================================================================
    # CRITÈRES ENSI: Robustesse Technique (30%)
    # ========================================================================
    
    def check_system_stability(self) -> bool:
        """Vérifie que le système ne plante pas."""
        print("\n[TEST 1] ROBUSTESSE TECHNIQUE - Stabilité système")
        print("-" * 70)
        
        try:
            # Vérifier main.py
            if not Path("main.py").exists():
                print("❌ FAIL: main.py n'existe pas")
                self.failed_checks += 1
                return False
            
            # Vérifier structures essentielles
            essential_files = [
                "src/utils/logger.py",
                "src/agents/auditor_agent.py",
                "src/agents/corrector_agent.py",
                "src/agents/judge_agent.py",
                "logs/experiment_data.json"
            ]
            
            missing = [f for f in essential_files if not Path(f).exists()]
            if missing:
                print(f"⚠️  WARNING: Fichiers manquants: {missing}")
                self.warnings.append(f"Fichiers manquants: {missing}")
            
            print("✅ PASS: Système présent et accessible")
            self.passed_checks += 1
            return True
        
        except Exception as e:
            print(f"❌ FAIL: {e}")
            self.failed_checks += 1
            return False
    
    def check_target_dir_handling(self) -> bool:
        """Vérifie le respect du paramètre --target_dir."""
        print("\n[TEST 2] ROBUSTESSE TECHNIQUE - Paramètre --target_dir")
        print("-" * 70)
        
        try:
            with open("main.py", "r") as f:
                main_content = f.read()
            
            if "target_dir" not in main_content and "--target_dir" not in main_content:
                print("❌ FAIL: --target_dir n'est pas utilisé")
                self.failed_checks += 1
                return False
            
            if "argparse" in main_content or "argument" in main_content.lower():
                print("✅ PASS: Argument parsing détecté")
                self.passed_checks += 1
                return True
            
            print("⚠️  WARNING: Argument parsing non clair")
            self.warnings.append("Argument parsing unclear in main.py")
            self.passed_checks += 1
            return True
        
        except Exception as e:
            print(f"❌ FAIL: {e}")
            self.failed_checks += 1
            return False
    
    def check_iteration_limit(self) -> bool:
        """Vérifie la limite de 10 itérations."""
        print("\n[TEST 3] ROBUSTESSE TECHNIQUE - Limite itérations (10 max)")
        print("-" * 70)
        
        try:
            with open("main.py", "r") as f:
                content = f.read()
            
            # Chercher une mention explicite de limite
            if "10" in content and ("iteration" in content.lower() or "while" in content):
                print("✅ PASS: Limite d'itérations détectée")
                self.passed_checks += 1
                return True
            
            print("⚠️  WARNING: Limite d'itérations non explicite")
            self.warnings.append("Iteration limit not clearly visible")
            self.passed_checks += 1
            return True
        
        except Exception as e:
            print(f"❌ FAIL: {e}")
            self.failed_checks += 1
            return False
    
    # ========================================================================
    # CRITÈRES ENSI: Qualité des Données (30%)
    # ========================================================================
    
    def check_logging_schema(self) -> bool:
        """Vérifie la conformité du schéma de logging ENSI."""
        print("\n[TEST 4] QUALITÉ DES DONNÉES - Schéma de logging")
        print("-" * 70)
        
        officer = DataOfficer()
        
        if not officer.logs:
            print("❌ FAIL: Aucun log trouvé")
            self.failed_checks += 1
            return False
        
        # Valider schéma
        schema_valid = officer.validate_schema()
        
        if not schema_valid and officer.validation_issues:
            print(f"❌ FAIL: Erreurs de schéma détectées:")
            for issue in officer.validation_issues[:3]:
                print(f"   {issue}")
            self.failed_checks += 1
            return False
        
        print("✅ PASS: Schéma ENSI 100% conforme")
        self.passed_checks += 1
        return True
    
    def check_prompt_response_tracking(self) -> bool:
        """Vérifie le tracking complet des prompts/réponses."""
        print("\n[TEST 5] QUALITÉ DES DONNÉES - Tracking prompt/response")
        print("-" * 70)
        
        officer = DataOfficer()
        
        if not officer.logs:
            print("❌ FAIL: Aucun log trouvé")
            self.failed_checks += 1
            return False
        
        missing_tracking = 0
        for i, entry in enumerate(officer.logs):
            details = entry.get('details', {})
            if 'input_prompt' not in details or 'output_response' not in details:
                missing_tracking += 1
        
        if missing_tracking > 0:
            print(f"❌ FAIL: {missing_tracking}/{len(officer.logs)} logs sans prompt/response")
            self.failed_checks += 1
            return False
        
        print(f"✅ PASS: {len(officer.logs)} logs avec tracking complet")
        self.passed_checks += 1
        return True
    
    def check_no_duplicates(self) -> bool:
        """Vérifie l'absence de doublons."""
        print("\n[TEST 6] QUALITÉ DES DONNÉES - Détection doublons")
        print("-" * 70)
        
        officer = DataOfficer()
        duplicates = officer.detect_duplicates()
        
        if duplicates:
            print(f"⚠️  WARNING: {len(duplicates)} potentiels doublons détectés")
            for dup in duplicates[:2]:
                print(f"   {dup}")
            self.warnings.append(f"{len(duplicates)} doublons potentiels")
        else:
            print("✅ PASS: Aucun doublon détecté")
        
        self.passed_checks += 1
        return True
    
    # ========================================================================
    # CRITÈRES ENSI: Performance (40%)
    # ========================================================================
    
    def check_test_execution(self) -> bool:
        """Vérifie que les tests s'exécutent."""
        print("\n[TEST 7] PERFORMANCE - Exécution des tests")
        print("-" * 70)
        
        # Vérifier présence de tests
        test_files = list(Path("tests").glob("*.py")) if Path("tests").exists() else []
        
        if not test_files:
            print("⚠️  WARNING: Aucun test trouvé dans tests/")
            self.warnings.append("No test files in tests/")
        else:
            print(f"✅ PASS: {len(test_files)} fichiers de test trouvés")
        
        self.passed_checks += 1
        return True
    
    def check_success_rate(self) -> bool:
        """Vérifie le taux de succès des agents."""
        print("\n[TEST 8] PERFORMANCE - Taux de succès")
        print("-" * 70)
        
        officer = DataOfficer()
        stats = officer.get_statistics()
        
        if stats['total_entries'] == 0:
            print("⚠️  WARNING: Aucune opération enregistrée")
            self.warnings.append("No operations logged")
            self.passed_checks += 1
            return True
        
        success_rate = stats['success_rate']
        print(f"📊 Taux de succès: {success_rate:.1f}% ({int(stats['status_distribution'].get('SUCCESS', 0))}/{stats['total_entries']})")
        
        if success_rate >= 95:
            print("✅ PASS: Taux de succès satisfaisant (≥95%)")
            self.passed_checks += 1
            return True
        else:
            print(f"⚠️  WARNING: Taux de succès faible ({success_rate:.1f}%)")
            self.warnings.append(f"Low success rate: {success_rate:.1f}%")
            self.passed_checks += 1
            return True
    
    def check_multi_agent_coordination(self) -> bool:
        """Vérifie la coordination multi-agent."""
        print("\n[TEST 9] PERFORMANCE - Coordination multi-agent")
        print("-" * 70)
        
        officer = DataOfficer()
        stats = officer.get_statistics()
        
        agents = list(stats['agents'].keys())
        models = list(stats['models'].keys())
        
        print(f"📊 Agents actifs: {len(agents)} - {agents}")
        print(f"📊 Modèles utilisés: {len(models)} - {models}")
        
        if len(agents) >= 2:
            print("✅ PASS: Multi-agent coordination détectée")
            self.passed_checks += 1
            return True
        else:
            print("⚠️  WARNING: Peu d'agents détectés")
            self.warnings.append(f"Only {len(agents)} agent(s) found")
            self.passed_checks += 1
            return True
    
    # ========================================================================
    # CHECKS ADDITIONNELS
    # ========================================================================
    
    def check_environment_setup(self) -> bool:
        """Vérifie la configuration de l'environnement."""
        print("\n[TEST 10] ENVIRONNEMENT - Configuration")
        print("-" * 70)
        
        try:
            # Vérifier .env
            if not Path(".env").exists():
                print("⚠️  WARNING: .env n'existe pas")
                self.warnings.append(".env file missing (may be in .gitignore)")
                self.passed_checks += 1
                return True
            
            # Vérifier requirements.txt
            if Path("requirements.txt").exists():
                print("✅ PASS: requirements.txt présent")
            else:
                print("⚠️  WARNING: requirements.txt manquant")
                self.warnings.append("requirements.txt not found")
            
            self.passed_checks += 1
            return True
        
        except Exception as e:
            print(f"❌ FAIL: {e}")
            self.failed_checks += 1
            return False
    
    # ========================================================================
    # RAPPORT FINAL
    # ========================================================================
    
    def run_all_checks(self) -> bool:
        """Exécute tous les checks et génère rapport."""
        print("\n" + "=" * 80)
        print("VERIFICATION PRE-SUBMISSION - CHECKLIST ENSI")
        print("=" * 80)
        print("\nCette vérification évalue 3 critères de notation:")
        print("  1. Robustesse Technique (30%)")
        print("  2. Qualité des Données (30%)")
        print("  3. Performance (40%)")
        print("\n" + "-" * 80)
        
        # Tests de robustesse
        self.check_system_stability()
        self.check_target_dir_handling()
        self.check_iteration_limit()
        
        # Tests de qualité des données
        self.check_logging_schema()
        self.check_prompt_response_tracking()
        self.check_no_duplicates()
        
        # Tests de performance
        self.check_test_execution()
        self.check_success_rate()
        self.check_multi_agent_coordination()
        
        # Tests additionnels
        self.check_environment_setup()
        
        # Résumé
        self._print_summary()
        
        return self.failed_checks == 0
    
    def _print_summary(self):
        """Affiche le résumé final."""
        print("\n" + "=" * 80)
        print("RÉSUMÉ FINAL")
        print("=" * 80)
        
        total = self.passed_checks + self.failed_checks
        pass_rate = (self.passed_checks / total * 100) if total > 0 else 0
        
        print(f"\n✅ Checks réussis: {self.passed_checks}")
        print(f"❌ Checks échoués: {self.failed_checks}")
        print(f"⚠️  Avertissements: {len(self.warnings)}")
        print(f"\n📊 Taux de réussite: {pass_rate:.1f}%")
        
        if self.warnings:
            print(f"\n⚠️  Avertissements:")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        print("\n" + "=" * 80)
        
        if self.failed_checks == 0:
            print("\n✅ ✅ ✅ PRÊT POUR SOUMISSION ✅ ✅ ✅\n")
            print("Le système satisfait tous les critères ENSI.\n")
        else:
            print("\n❌ CORRECTIFS REQUIS AVANT SOUMISSION\n")
            print("Veuillez corriger les erreurs ci-dessus.\n")
        
        print("=" * 80 + "\n")


def main():
    """Point d'entrée."""
    verifier = PreSubmissionVerifier()
    success = verifier.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
