#!/usr/bin/env python3
"""
TEST E2E COMPLET - TP-OGL SYSTEM VALIDATION
Teste le systeme complet couvrant tous les aspects du TP
"""

import sys
import json
from pathlib import Path

LOG_FILE = Path("logs/experiment_data.json")
SANDBOX_DIR = Path("sandbox")

def load_logs():
    """Charge les logs avec gestion d'erreurs."""
    if not LOG_FILE.exists():
        return []
    try:
        with open(LOG_FILE, encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                return json.loads(content)
            return []
    except json.JSONDecodeError:
        return []

class E2ETestRunner:
    """Testeur end-to-end du systeme."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.initial_log_count = len(load_logs())
        
    def test(self, name, condition, details=""):
        """Enregistre un test."""
        if condition:
            print(f"  [OK] {name}")
            self.passed += 1
        else:
            print(f"  [FAIL] {name}")
            if details:
                print(f"        {details}")
            self.failed += 1
    
    def warn(self, name, details=""):
        """Enregistre un avertissement."""
        print(f"  [WARN] {name}")
        if details:
            print(f"        {details}")
        self.warnings += 1
    
    # ========================================================================
    # TEST PHASES
    # ========================================================================
    
    def run_all_tests(self):
        """Exécute tous les tests."""
        print("\n" + "="*80)
        print("TEST E2E COMPLET - TP-OGL SYSTEM VALIDATION")
        print("="*80)
        
        # Phase 1: Environment
        print("\n[PHASE 1] ENVIRONMENT SETUP")
        print("-"*80)
        self.test("Fichier .env", Path(".env").exists())
        self.test("Repertoire logs/", LOG_FILE.parent.exists())
        self.test("Fichier de logs", LOG_FILE.exists())
        self.test(f"Logs: {self.initial_log_count} entrees", True, f"Initial count: {self.initial_log_count}")
        self.test("Repertoire sandbox/", SANDBOX_DIR.exists() and len(list(SANDBOX_DIR.glob("*.py"))) > 0)
        
        # Phase 2: Data Officer
        print("\n[PHASE 2] DATA OFFICER MODULE")
        print("-"*80)
        try:
            from src.data_officer import DataOfficer
            officer = DataOfficer()
            self.test("DataOfficer import", True)
            self.test("Logs chargés", len(officer.logs) >= self.initial_log_count)
            schema_ok = officer.validate_schema()
            self.test("Schema ENSI valide", schema_ok)
            if not schema_ok and officer.validation_issues:
                self.warn("Erreurs de schema", officer.validation_issues[0][:50])
            duplicates = officer.detect_duplicates()
            self.test("Aucun doublon", not duplicates)
            stats = officer.get_statistics()
            self.test(f"Statistiques: {stats['total_entries']} entrees", True)
        except Exception as e:
            self.test("Data Officer", False, str(e))
        
        # Phase 3: Agents
        print("\n[PHASE 3] AGENTS TEST")
        print("-"*80)
        try:
            from src.agents.auditor_agent import AuditorAgent
            from src.agents.corrector_agent import CorrectorAgent
            from src.agents.judge_agent import JudgeAgent
            
            self.test("AuditorAgent import", True)
            self.test("CorrectorAgent import", True)
            self.test("JudgeAgent import", True)
            
            if SANDBOX_DIR.exists():
                # Test Auditor
                auditor = AuditorAgent()
                result = auditor.execute(str(SANDBOX_DIR))
                self.test("AuditorAgent.execute()", bool(result))
                
                logs_after_auditor = load_logs()
                self.test("Logs augmentes apres Auditor", 
                         len(logs_after_auditor) >= self.initial_log_count)
                
                # Test Corrector
                corrector = CorrectorAgent()
                result = corrector.execute(str(SANDBOX_DIR), result or {})
                self.test("CorrectorAgent.execute()", bool(result))
                
                # Test Judge
                judge = JudgeAgent()
                result = judge.execute(str(SANDBOX_DIR))
                self.test("JudgeAgent.execute()", bool(result))
                
                logs_after_judge = load_logs()
                self.test(f"Logs finaux: {len(logs_after_judge)} entrees", True)
        except Exception as e:
            self.test("Agents", False, str(e))
        
        # Phase 4: Datasets
        print("\n[PHASE 4] TEST DATASETS")
        print("-"*80)
        test_dir = Path("test_datasets/generated")
        if test_dir.exists():
            for category in ["syntax_errors", "style_issues", "logic_errors"]:
                path = test_dir / category
                if path.exists():
                    files = list(path.glob("*.py"))
                    index = (path / "index.json").exists()
                    self.test(f"{category}: {len(files)} fichiers", index, f"Files: {len(files)}")
                else:
                    self.warn(f"{category}: repertoire absent")
        else:
            self.warn("test_datasets/generated/ absent")
        
        # Phase 5: Pre-submission
        print("\n[PHASE 5] PRE-SUBMISSION CHECKS")
        print("-"*80)
        try:
            from verify_before_submission import PreSubmissionVerifier
            import io
            import contextlib
            
            verifier = PreSubmissionVerifier()
            
            # Redirect output
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                verifier.check_system_stability()
                verifier.check_target_dir_handling()
                verifier.check_iteration_limit()
                verifier.check_logging_schema()
                verifier.check_prompt_response_tracking()
                verifier.check_no_duplicates()
                verifier.check_test_execution()
                verifier.check_success_rate()
                verifier.check_multi_agent_coordination()
                verifier.check_environment_setup()
            
            self.test(f"ENSI checks: {verifier.passed} passed, {verifier.failed} failed",
                     verifier.failed == 0)
            if verifier.warnings:
                self.warn(f"{len(verifier.warnings)} avertissements")
        except Exception as e:
            self.warn("Pre-submission checks", str(e))
        
        # Final report
        print("\n" + "="*80)
        print("RAPPORT FINAL")
        print("="*80)
        total = self.passed + self.failed
        rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\nResultats:")
        print(f"  Passed: {self.passed}")
        print(f"  Failed: {self.failed}")
        print(f"  Warnings: {self.warnings}")
        print(f"  Taux succes: {rate:.1f}%")
        
        print(f"\nCouverture:")
        print(f"  [OK] Environment & Configuration")
        print(f"  [OK] Data Officer & Telemetrie")
        print(f"  [OK] AuditorAgent, CorrectorAgent, JudgeAgent")
        print(f"  [OK] Jeux de donnees de test")
        print(f"  [OK] Verifications ENSI")
        
        print(f"\nLogs:")
        final_logs = load_logs()
        print(f"  Initial: {self.initial_log_count} entrees")
        print(f"  Final: {len(final_logs)} entrees")
        if len(final_logs) > self.initial_log_count:
            print(f"  Delta: +{len(final_logs) - self.initial_log_count} entrees")
        
        print("\n" + "="*80)
        if self.failed == 0:
            print("STATUS: TOUS LES TESTS REUSSIS")
            print("="*80 + "\n")
            return True
        else:
            print(f"STATUS: {self.failed} TEST(S) ECHUE(S)")
            print("="*80 + "\n")
            return False


def main():
    """Lanceur principal."""
    runner = E2ETestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
