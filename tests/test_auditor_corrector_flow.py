"""
Integration tests for Improved Auditor → Corrector flow (Phase 2 core agents).
Tests that agents use Phase 1 tools and logging correctly with all improvements.

Run with: pytest test_improved_agents_integration.py -v
"""

import os
import json
import tempfile
from pathlib import Path
import pytest

from src.agents.auditor_agent import AuditorAgent, AuditorReport, ASTAnalyzer
from src.agents.corrector_agent import CorrectorAgent, CorrectionPlan, ASTTransformer
from src.utils.logger import log_experiment, ActionType


class TestASTAnalyzer:
    """Test AST-based analysis utilities."""
    
    def test_bare_except_detection(self):
        """Test accurate bare except detection using AST."""
        code_with_bare = """
try:
    risky()
except:
    pass
"""
        assert ASTAnalyzer.has_bare_except(code_with_bare) == True
    
    def test_no_false_positive_in_comments(self):
        """Test that comments don't trigger false positives."""
        code_with_comment = """
# This has except: in comment but not in code
try:
    safe()
except ValueError:
    pass
"""
        assert ASTAnalyzer.has_bare_except(code_with_comment) == False
    
    def test_no_false_positive_in_strings(self):
        """Test that strings don't trigger false positives."""
        code_with_string = '''
message = "The code has except: in a string"
try:
    safe()
except ValueError:
    pass
'''
        assert ASTAnalyzer.has_bare_except(code_with_string) == False
    
    def test_print_detection(self):
        """Test print statement detection."""
        code_with_print = """
def debug():
    print("Hello")
    print("World")
"""
        assert ASTAnalyzer.has_print_statements(code_with_print) == True
    
    def test_print_with_logging_ok(self):
        """Test print is OK when logging is imported."""
        code_with_logging = """
import logging

def debug():
    print("Hello")  # OK because logging is imported
"""
        assert ASTAnalyzer.has_print_statements(code_with_logging) == False
    
    def test_function_complexity_detection(self):
        """Test detection of complex functions."""
        code_with_long_function = """
def complex_function():
""" + "\n".join([f"    line_{i} = {i}" for i in range(60)]) + """
    return True
"""
        complexities = ASTAnalyzer.get_function_complexities(code_with_long_function)
        assert len(complexities) == 1
        assert complexities[0][0] == "complex_function"
        assert complexities[0][1] > 50
    
    def test_todo_comment_detection(self):
        """Test TODO comment detection."""
        code_with_todo = """
def incomplete():
    # TODO: implement this
    pass
"""
        assert ASTAnalyzer.has_todo_comments(code_with_todo) == True


class TestASTTransformer:
    """Test AST-based code transformations."""
    
    def test_fix_bare_except(self):
        """Test bare except fixing using AST."""
        code = """
try:
    risky()
except:
    pass
"""
        fixed, changed = ASTTransformer.fix_bare_except(code)
        assert changed == True
        assert "except Exception as e:" in fixed
        assert "except:" not in fixed
    
    def test_no_change_when_already_good(self):
        """Test no changes when code is already good."""
        code = """
try:
    safe()
except ValueError as e:
    handle(e)
"""
        fixed, changed = ASTTransformer.fix_bare_except(code)
        assert changed == False
        assert fixed == code
    
    def test_multiple_bare_excepts(self):
        """Test fixing multiple bare excepts."""
        code = """
def function1():
    try:
        risky1()
    except:
        pass

def function2():
    try:
        risky2()
    except:
        pass
"""
        fixed, changed = ASTTransformer.fix_bare_except(code)
        assert changed == True
        assert fixed.count("except Exception as e:") == 2
        assert "except:" not in fixed
    
    def test_replace_print_with_logging(self):
        """Test print replacement with logging."""
        code = """
def debug():
    print("Hello")
    print("World")
"""
        fixed, changed = ASTTransformer.replace_print_with_logging(code)
        assert changed == True
        assert "logging.debug" in fixed
        assert "import logging" in fixed
        assert "print(" not in fixed
    
    def test_preserve_existing_logging_import(self):
        """Test that existing logging imports are preserved."""
        code = """
import logging

def debug():
    print("Hello")
"""
        fixed, changed = ASTTransformer.replace_print_with_logging(code)
        assert changed == True
        # Should only have one logging import
        assert fixed.count("import logging") == 1


class TestAuditorAgentIntegration:
    """Test improved AuditorAgent with Phase 1 tools."""
    
    @pytest.fixture
    def temp_code_dir(self):
        """Create temporary directory with test Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files with various issues
            test_file1 = Path(tmpdir) / "module1.py"
            test_file1.write_text("""
def bad_function():
    try:
        print("doing something")
        return 42
    except:
        print("error occurred")
""")
            
            test_file2 = Path(tmpdir) / "module2.py"
            test_file2.write_text("""
class MyClass:
    def method1(self):
        pass
    
    def method2(self):
        # TODO: implement this
        pass
""")
            
            # File with complex function
            test_file3 = Path(tmpdir) / "module3.py"
            lines = ["def very_long_function():"]
            lines.extend([f"    line_{i} = {i}" for i in range(120)])
            lines.append("    return True")
            test_file3.write_text("\n".join(lines))
            
            yield tmpdir
    
    def test_auditor_analyzes_files(self, temp_code_dir):
        """Test auditor can analyze files in directory."""
        auditor = AuditorAgent()
        result = auditor.execute(temp_code_dir)
        
        assert result["status"] == "audit_complete"
        assert result["files_audited"] >= 3
        assert isinstance(result["all_issues"], list)
        assert isinstance(result["file_results"], dict)
    
    def test_auditor_detects_issues_accurately(self, temp_code_dir):
        """Test auditor finds code issues using AST (no false positives)."""
        auditor = AuditorAgent()
        result = auditor.execute(temp_code_dir)
        
        # Should find issues: bare except, print, TODO, long function
        assert result["total_issues"] > 0
        assert len(result["all_issues"]) > 0
        
        # Check specific issues are detected
        all_issues_str = " ".join(result["all_issues"]).lower()
        assert "bare except" in all_issues_str or "print" in all_issues_str
    
    def test_auditor_parallel_processing(self, temp_code_dir):
        """Test parallel processing works correctly."""
        auditor = AuditorAgent(max_workers=2)
        
        # Test parallel
        result_parallel = auditor.execute(temp_code_dir, parallel=True)
        
        # Test sequential
        result_sequential = auditor.execute(temp_code_dir, parallel=False)
        
        # Results should be identical (regardless of order)
        assert result_parallel["files_audited"] == result_sequential["files_audited"]
        assert result_parallel["total_issues"] == result_sequential["total_issues"]
    
    def test_auditor_handles_errors_gracefully(self):
        """Test auditor handles invalid input gracefully."""
        auditor = AuditorAgent()
        
        # Test non-existent directory
        with pytest.raises(ValueError, match="does not exist"):
            auditor.execute("/nonexistent/directory")
        
        # Test file instead of directory
        with tempfile.NamedTemporaryFile() as tmpfile:
            with pytest.raises(ValueError, match="not a directory"):
                auditor.execute(tmpfile.name)
    
    def test_auditor_validates_file_paths(self, temp_code_dir):
        """Test path traversal protection."""
        from src.agents.auditor_agent import validate_file_path
        
        base_path = Path(temp_code_dir)
        
        # Valid paths
        assert validate_file_path(base_path, "module1.py") == True
        assert validate_file_path(base_path, "subdir/file.py") == True
        
        # Invalid paths (path traversal attempts)
        assert validate_file_path(base_path, "../etc/passwd") == False
        assert validate_file_path(base_path, "../../sensitive.py") == False
    
    def test_auditor_logs_analysis_action(self, temp_code_dir):
        """Test auditor logs ANALYSIS actions correctly."""
        auditor = AuditorAgent("TestAuditor", "test-model")
        result = auditor.execute(temp_code_dir)
        
        # Check logs exist
        assert os.path.exists("logs/experiment_data.json")
        
        with open("logs/experiment_data.json") as f:
            logs = json.load(f)
        
        # Find audit logs
        audit_logs = [l for l in logs if l["agent"] == "TestAuditor"]
        assert len(audit_logs) > 0
        
        # Verify structure
        for log in audit_logs:
            assert "input_prompt" in log["details"]
            assert "output_response" in log["details"]
            assert log["action"] == "CODE_ANALYSIS"
    
    def test_auditor_report_extraction(self, temp_code_dir):
        """Test AuditorReport can extract findings."""
        auditor = AuditorAgent()
        result = auditor.execute(temp_code_dir)
        report = AuditorReport(result)
        
        # Test report methods
        critical = report.get_critical_issues()
        assert isinstance(critical, list)
        
        files_by_count = report.get_files_by_issue_count()
        assert isinstance(files_by_count, list)
        
        avg_score = report.get_average_pylint_score()
        assert isinstance(avg_score, float)
        
        # Test dict conversion
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert "files_audited" in report_dict
        assert "total_issues" in report_dict
    
    def test_auditor_empty_directory(self):
        """Test auditor handles empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            auditor = AuditorAgent()
            result = auditor.execute(tmpdir)
            
            assert result["status"] == "no_files_found"
            assert result["files_audited"] == 0


class TestCorrectorAgentIntegration:
    """Test improved CorrectorAgent with Phase 1 tools."""
    
    @pytest.fixture
    def temp_code_dir(self):
        """Create temporary directory with test Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "module.py"
            test_file.write_text("""
def function_with_issues():
    try:
        print("test")
        result = process()
        print("result:", result)
    except:
        pass
""")
            yield tmpdir
    
    @pytest.fixture
    def audit_output(self, temp_code_dir):
        """Get audit output to feed to corrector."""
        auditor = AuditorAgent()
        return auditor.execute(temp_code_dir)
    
    def test_corrector_validates_audit_report(self, temp_code_dir):
        """Test corrector validates audit report structure."""
        corrector = CorrectorAgent()
        
        # Invalid report (missing required keys)
        invalid_report = {"some_key": "some_value"}
        
        with pytest.raises(ValueError, match="missing required keys"):
            corrector.execute(temp_code_dir, invalid_report)
    
    def test_corrector_takes_audit_input(self, temp_code_dir, audit_output):
        """Test corrector accepts audit report as input."""
        corrector = CorrectorAgent()
        result = corrector.execute(temp_code_dir, audit_output)
        
        assert result["status"] == "correction_complete"
        assert result["total_corrections"] >= 0
        assert isinstance(result["corrections"], dict)
    
    def test_corrector_generates_corrections(self, temp_code_dir, audit_output):
        """Test corrector generates corrections for found issues."""
        corrector = CorrectorAgent()
        result = corrector.execute(temp_code_dir, audit_output)
        
        # If audit found issues, corrector should generate corrections
        if audit_output["total_issues"] > 0:
            assert result["total_corrections"] > 0
    
    def test_corrector_applies_ast_transformations(self, temp_code_dir, audit_output):
        """Test that corrector uses AST transformations."""
        corrector = CorrectorAgent()
        result = corrector.execute(temp_code_dir, audit_output)
        
        # Check that corrections were attempted
        for filename, file_result in result["corrections"].items():
            if file_result["status"] == "corrected":
                corrections = file_result["corrections"]
                for correction in corrections:
                    # Should have original and corrected code
                    assert "original_code" in correction
                    assert "corrected_code" in correction
                    assert "change_summary" in correction
    
    def test_corrector_handles_errors_gracefully(self):
        """Test corrector handles invalid input gracefully."""
        corrector = CorrectorAgent()
        
        # Test non-existent directory
        with pytest.raises(ValueError, match="does not exist"):
            corrector.execute("/nonexistent/directory", {
                "all_issues": [],
                "file_results": {}
            })
    
    def test_corrector_retry_logic(self):
        """Test corrector retry logic."""
        corrector = CorrectorAgent()
        
        # Should retry on recoverable errors
        assert corrector.can_retry("needs_iteration") == True
        assert corrector.can_retry("incomplete, try again") == True
        assert corrector.can_retry("timeout error") == True
        assert corrector.can_retry("temporary failure") == True
        
        # Should NOT retry on permanent errors
        assert corrector.can_retry("rejected") == False
        assert corrector.can_retry("invalid") == False
    
    def test_corrector_retry_execution(self, temp_code_dir, audit_output):
        """Test execute_with_retry method."""
        corrector = CorrectorAgent()
        
        # Should succeed on first try with valid input
        result = corrector.execute_with_retry(
            temp_code_dir, 
            audit_output,
            max_retries=3
        )
        
        assert result["status"] == "correction_complete"
    
    def test_corrector_logs_generation_action(self, temp_code_dir, audit_output):
        """Test corrector logs CODE_GEN actions correctly."""
        corrector = CorrectorAgent("TestCorrector", "test-model")
        result = corrector.execute(temp_code_dir, audit_output)
        
        # Check logs
        assert os.path.exists("logs/experiment_data.json")
        
        with open("logs/experiment_data.json") as f:
            logs = json.load(f)
        
        # Find correction logs
        correction_logs = [l for l in logs if l["agent"] == "TestCorrector"]
        assert len(correction_logs) > 0
        
        # Verify CODE_GEN action
        for log in correction_logs:
            assert "input_prompt" in log["details"]
            assert "output_response" in log["details"]
            assert log["action"] == "CODE_GEN"
    
    def test_correction_plan_methods(self, temp_code_dir, audit_output):
        """Test CorrectionPlan utility methods."""
        corrector = CorrectorAgent()
        result = corrector.execute(temp_code_dir, audit_output)
        plan = CorrectionPlan(result)
        
        # Test all methods
        refactored = plan.get_refactored_files()
        assert isinstance(refactored, list)
        
        total_changes = plan.get_total_changes()
        assert isinstance(total_changes, int)
        
        by_file = plan.get_corrections_by_file()
        assert isinstance(by_file, dict)
        
        errors = plan.get_files_with_errors()
        assert isinstance(errors, list)
        
        lines_changed = plan.get_total_lines_changed()
        assert isinstance(lines_changed, int)
        
        # Test dict conversion
        plan_dict = plan.to_dict()
        assert isinstance(plan_dict, dict)
        assert "files_corrected" in plan_dict
        assert "ready_for_review" in plan_dict


class TestAuditorCorrectorFlow:
    """Integration test: Improved Auditor → Corrector flow."""
    
    @pytest.fixture
    def test_code_dir(self):
        """Create test code structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple files with various issues
            for i in range(3):
                test_file = Path(tmpdir) / f"module{i}.py"
                test_file.write_text(f"""
def function{i}():
    try:
        result = process_data()
        print("Result:", result)
        return result
    except:
        print("Error in function{i}")
        return None

class Class{i}:
    def __init__(self):
        self.data = []
    
    def add(self, value):
        self.data.append(value)
        print(f"Added {{value}}")
""")
            yield tmpdir
    
    def test_full_audit_correction_flow(self, test_code_dir):
        """Test complete flow: audit → get report → correct → get plan."""
        # Step 1: Audit
        auditor = AuditorAgent("FlowAuditor")
        audit_result = auditor.execute(test_code_dir)
        audit_report = AuditorReport(audit_result)
        
        assert audit_result["status"] == "audit_complete"
        assert audit_result["files_audited"] >= 3
        
        # Verify report methods
        critical = audit_report.get_critical_issues()
        assert isinstance(critical, list)
        
        # Step 2: Correct
        corrector = CorrectorAgent("FlowCorrector")
        correction_result = corrector.execute(test_code_dir, audit_result)
        correction_plan = CorrectionPlan(correction_result)
        
        assert correction_result["status"] == "correction_complete"
        
        # Verify plan methods
        refactored = correction_plan.get_refactored_files()
        assert isinstance(refactored, list)
        
        # Step 3: Verify both logged correctly
        assert os.path.exists("logs/experiment_data.json")
        
        with open("logs/experiment_data.json") as f:
            logs = json.load(f)
        
        auditor_logs = [l for l in logs if l["agent"] == "FlowAuditor"]
        corrector_logs = [l for l in logs if l["agent"] == "FlowCorrector"]
        
        assert len(auditor_logs) > 0, "Auditor should have logged actions"
        assert len(corrector_logs) > 0, "Corrector should have logged actions"
        
        # Verify action types
        for log in auditor_logs:
            assert log["action"] == "CODE_ANALYSIS"
        
        for log in corrector_logs:
            assert log["action"] == "CODE_GEN"
    
    def test_parallel_audit_sequential_correct(self, test_code_dir):
        """Test parallel audit followed by sequential correction."""
        # Parallel audit
        auditor = AuditorAgent("ParallelAuditor", max_workers=4)
        audit_result = auditor.execute(test_code_dir, parallel=True)
        
        # Sequential correction
        corrector = CorrectorAgent("SequentialCorrector")
        correction_result = corrector.execute(test_code_dir, audit_result)
        
        assert audit_result["status"] == "audit_complete"
        assert correction_result["status"] == "correction_complete"
    
    def test_logs_contain_prompts_and_responses(self, test_code_dir):
        """Verify mandatory logging fields (input_prompt, output_response)."""
        auditor = AuditorAgent("PromptAuditor")
        audit_result = auditor.execute(test_code_dir)
        
        corrector = CorrectorAgent("PromptCorrector")
        corrector.execute(test_code_dir, audit_result)
        
        with open("logs/experiment_data.json") as f:
            logs = json.load(f)
        
        # Filter to only agent logs
        agent_logs = [l for l in logs if l["agent"] in ["PromptAuditor", "PromptCorrector"]]
        assert len(agent_logs) > 0, "No agent logs found"
        
        for log in agent_logs:
            # Mandatory fields
            assert "agent" in log
            assert "model" in log
            assert "action" in log
            assert "status" in log
            assert "details" in log
            
            # Mandatory details fields
            details = log["details"]
            assert "input_prompt" in details, f"Missing input_prompt in {log['agent']}"
            assert "output_response" in details, f"Missing output_response in {log['agent']}"
            
            # Should not be empty
            assert len(str(details["input_prompt"])) > 0
            assert len(str(details["output_response"])) > 0
    
    def test_end_to_end_correction_quality(self, test_code_dir):
        """Test that corrections actually fix issues."""
        # Run audit
        auditor = AuditorAgent()
        audit_result = auditor.execute(test_code_dir)
        
        # Run correction
        corrector = CorrectorAgent()
        correction_result = corrector.execute(test_code_dir, audit_result)
        
        # Verify corrections were made
        for filename, file_result in correction_result["corrections"].items():
            if file_result["status"] == "corrected":
                for correction in file_result["corrections"]:
                    original = correction["original_code"]
                    corrected = correction["corrected_code"]
                    
                    # If it was a bare except fix, verify it's fixed
                    if "bare_except" in correction["issue"].lower():
                        assert "except:" not in corrected or "except Exception" in corrected
                    
                    # If it was a print fix, verify logging is added
                    if "print" in correction["issue"].lower():
                        if correction["status"] == "corrected":
                            assert "logging" in corrected or "# logging" in corrected


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_auditor_with_syntax_errors(self):
        """Test auditor handles files with syntax errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_file = Path(tmpdir) / "bad.py"
            bad_file.write_text("def broken(\n  syntax error here")
            
            auditor = AuditorAgent()
            result = auditor.execute(tmpdir)
            
            # Should complete without crashing
            assert result["status"] in ["audit_complete", "no_files_found"]
    
    def test_corrector_with_empty_audit(self):
        """Test corrector with audit that found no issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            good_file = Path(tmpdir) / "good.py"
            good_file.write_text("""
import logging

def perfect_function():
    logging.info("Everything is great")
    return True
""")
            
            auditor = AuditorAgent()
            audit_result = auditor.execute(tmpdir)
            
            corrector = CorrectorAgent()
            correction_result = corrector.execute(tmpdir, audit_result)
            
            # Should handle gracefully
            assert correction_result["status"] == "correction_complete"
    
    def test_unicode_handling(self):
        """Test that agents handle Unicode correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            unicode_file = Path(tmpdir) / "unicode.py"
            unicode_file.write_text("""
# -*- coding: utf-8 -*-
def greet():
    message = "Hello, 世界! 🌍"
    print(message)
""", encoding="utf-8")
            
            auditor = AuditorAgent()
            result = auditor.execute(tmpdir)
            
            assert result["status"] == "audit_complete"
            # Should detect print statement
            assert result["total_issues"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])