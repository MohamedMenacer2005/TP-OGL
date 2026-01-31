"""
Corrector Agent - Simplified Version
Applies mechanical refactors and delegates semantic fixes to LLM.
No hardcoded logic fixes - pure delegation.
"""

from dotenv import load_dotenv
load_dotenv()

from src.agents.base_agent import BaseAgent
from src.utils.logger import ActionType
from src.utils.code_reader import CodeReader
from src.utils.llm_client import LLMClient
from typing import Dict, List
from pathlib import Path


class CorrectorAgent(BaseAgent):
    """
    CorrectorAgent:
    - Applies AST-safe mechanical fixes (placeholder for future)
    - Delegates logic repair to LLM
    - No hardcoded pattern matching
    """

    def __init__(self, model: str = "models/gemini-2.0-flash"):
        super().__init__(agent_name="CorrectorAgent", model=model)
        self.model = model
        self.llm_client = LLMClient(model=model)

    def analyze(self, code: str, filename: str = "unknown.py") -> dict:
        """
        Corrector does not perform analysis.
        Analysis must be provided externally (Auditor or Judge).
        """
        return {}

    def execute(self, target_dir: str, issue_report: Dict) -> Dict:
        """
        Execute corrections based on provided issues.
        
        Args:
            target_dir: Directory containing code to fix
            issue_report: Dict with structure:
                {
                    "file_results": {
                        "filename": {
                            "analysis": {"issues": ["issue1", "issue2"]}
                        }
                    }
                }
        
        Returns:
            Dict with correction statistics
        """
        reader = CodeReader(target_dir)
        files = reader.read_all_python_files()

        total_corrections = 0
        corrected_files = {}
        files_corrected_count = 0

        for filename, content in files.items():
            file_issues = self._extract_file_issues(filename, issue_report)
            if not file_issues:
                continue

            original_code = content
            updated_code = content
            corrections_made = 0

            for issue_text in file_issues:
                # Determine issue type
                issue_type = self._classify_issue(issue_text)
                
                if issue_type == "mechanical":
                    # Placeholder for future AST-based fixes
                    updated_code = self._apply_mechanical_fix(
                        updated_code, issue_text, filename
                    )
                elif issue_type in ("logic", "test_failure", "semantic"):
                    # Delegate to LLM for semantic fixes
                    updated_code = self._apply_llm_logic_fix(
                        updated_code, issue_text, filename
                    )
                    corrections_made += 1

            # Write corrected code back to file
            if updated_code != original_code:
                file_path = Path(target_dir) / filename
                file_path.write_text(updated_code, encoding='utf-8')
                corrected_files[filename] = corrections_made
                total_corrections += corrections_made
                files_corrected_count += 1
                
                self.logger.info(f"✓ Corrected {filename}: {corrections_made} fixes applied")

        # Log summary
        self._log_action(
            action=ActionType.GENERATION,
            prompt=f"Generated corrections for {files_corrected_count} files",
            response=f"Created {total_corrections} corrections addressing {len(issue_report.get('all_issues', []))} critical issues",
            extra_details={
                "files_corrected": files_corrected_count,
                "total_corrections": total_corrections,
                "critical_issues_addressed": len(issue_report.get('all_issues', []))
            }
        )

        return {
            "files_corrected": files_corrected_count,
            "total_corrections": total_corrections,
            "details": corrected_files,
            "status": "success"
        }

    # ------------------------
    # Internal helpers
    # ------------------------

    def _classify_issue(self, issue_text: str) -> str:
        """
        Classify issue as mechanical or semantic/logic.
        
        Args:
            issue_text: Description of the issue
            
        Returns:
            "mechanical" or "logic"
        """
        # Mechanical issues (future AST-based fixes)
        mechanical_keywords = ["bare except", "print statement", "TODO comment"]
        
        if any(kw in issue_text.lower() for kw in mechanical_keywords):
            return "mechanical"
        
        # Everything else is semantic/logic (LLM-based)
        return "logic"

    def _extract_file_issues(self, filename: str, report: Dict) -> List[str]:
        """
        Extract issues for a specific file from report.
        
        Args:
            filename: Name of the file
            report: Issue report dict
            
        Returns:
            List of issue descriptions
        """
        file_data = report.get("file_results", {}).get(filename, {})
        
        # Try nested structure first (Auditor format)
        issues = file_data.get("analysis", {}).get("issues", [])
        
        # Fallback to flat structure
        if not issues:
            issues = file_data.get("issues", [])
        
        return issues

    def _apply_mechanical_fix(self, code: str, issue: str, filename: str) -> str:
        """
        Placeholder for AST-based fixes (safe transformations only).
        Future: Implement AST transformations for structural fixes.
        
        Args:
            code: Original code
            issue: Issue description
            filename: File being fixed
            
        Returns:
            Fixed code (currently unchanged)
        """
        self._log_action(
            action=ActionType.FIX,
            prompt=f"Apply mechanical fix: {issue}",
            response="Mechanical fix deferred (AST layer not implemented)",
            extra_details={"filename": filename, "issue": issue, "fix_type": "mechanical"}
        )
        
        # Placeholder - no mechanical fixes yet
        return code

    def _apply_llm_logic_fix(self, code: str, issue: str, filename: str) -> str:
        """
        Delegate semantic repair to LLM.
        
        Args:
            code: Original code
            issue: Issue description
            filename: File being fixed
            
        Returns:
            Fixed code from LLM
        """
        try:
            # Use LLMClient's generate_correction method
            fixed_code = self.llm_client.generate_correction(
                code=code,
                issue=issue,
                context=f"File: {filename}"
            )

            # Extract code from markdown if present
            if "```python" in fixed_code:
                start = fixed_code.find("```python") + len("```python")
                end = fixed_code.rfind("```")
                fixed_code = fixed_code[start:end].strip()

            # Validate syntax
            try:
                compile(fixed_code, "<string>", "exec")
            except SyntaxError as e:
                self.logger.warning(f"LLM generated invalid Python: {e}")
                return code  # Return original if fix is invalid

            # Log the fix
            self._log_action(
                action=ActionType.FIX,
                prompt=f"Fix for: {issue[:100]}",
                response=f"LLM generated semantic fix ({len(fixed_code)} chars)",
                extra_details={
                    "filename": filename,
                    "issue": issue,
                    "fix_type": "semantic_llm",
                    "original_length": len(code),
                    "fixed_length": len(fixed_code)
                }
            )

            return fixed_code

        except Exception as e:
            self.logger.error(f"LLM fix failed: {e}")
            self._log_action(
                action=ActionType.FIX,
                prompt=f"Attempted fix: {issue}",
                response=f"LLM fix failed: {str(e)}",
                extra_details={"filename": filename, "error": str(e)},
                status="FAILURE"
            )
            return code  # Return original on error
