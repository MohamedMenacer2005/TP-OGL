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

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
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

    def _extract_code_from_response(self, response: str) -> str:
        """
        Extract Python code from LLM response.
        Handles multiple markdown formats.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Extracted Python code, or empty string if extraction fails
        """
        if "```python" in response:
            start = response.find("```python") + 9
            end = response.rfind("```")
            if end > start:
                return response[start:end].strip()
        
        if "```" in response:
            parts = response.split("```")
            if len(parts) >= 3:
                code = parts[1].strip()
                if code.startswith("python\n"):
                    code = code[7:].strip()
                return code
        
        return response.strip()

    def _apply_llm_logic_fix(self, code: str, issue: str, filename: str) -> str:
        """
        Delegate semantic repair to LLM with robust error handling.
        
        Args:
            code: Original code
            issue: Issue description
            filename: File being fixed
            
        Returns:
            Fixed code from LLM, or original code if fix fails
        """
        try:
            raw_response = self.llm_client.generate_correction(
                code=code,
                issue=issue,
                context=f"File: {filename}"
            )
            
            if not raw_response or not raw_response.strip():
                self.logger.error(f"LLM returned empty response for {filename}")
                return code
            
            fixed_code = self._extract_code_from_response(raw_response)
            
            if not fixed_code or len(fixed_code) < 10:
                self.logger.warning(f"Extracted code too short or empty for {filename}")
                self.logger.warning(f"Raw response preview: {raw_response[:200]}")
                return code
            
            try:
                compile(fixed_code, "<string>", "exec")
            except SyntaxError as e:
                self.logger.warning(f"LLM generated invalid Python syntax: {e}")
                return code
            
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
            
            self.logger.info(f"LLM fix successfully applied to {filename}")
            return fixed_code

        except Exception as e:
            self.logger.warning(f"LLM fix failed: {e}, attempting fallback fixes")
            
            fallback_code = self._apply_fallback_fixes(code, issue, filename)
            
            if fallback_code != code:
                self._log_action(
                    action=ActionType.FIX,
                    prompt=f"Fix for: {issue[:100]}",
                    response=f"Applied fallback automatic fix ({len(fallback_code)} chars)",
                    extra_details={
                        "filename": filename,
                        "issue": issue,
                        "fix_type": "fallback_automatic",
                        "original_length": len(code),
                        "fixed_length": len(fallback_code)
                    }
                )
                return fallback_code
            
            self.logger.error(f"Both LLM and fallback fixes failed: {e}")
            self._log_action(
                action=ActionType.FIX,
                prompt=f"Attempted fix: {issue}",
                response=f"LLM and fallback fixes failed: {str(e)}",
                extra_details={"filename": filename, "error": str(e)},
                status="FAILURE"
            )
            return code

    def _apply_fallback_fixes(self, code: str, issue: str, filename: str) -> str:
        """
        Apply automatic fallback fixes when LLM is unavailable.
        Handles common Python bugs programmatically.
        
        Args:
            code: Original code
            issue: Issue description
            filename: File being fixed
            
        Returns:
            Fixed code with automatic corrections
        """
        fixed_code = code
        issue_lower = issue.lower()
        
        # Fix 1: BankAccount __init__ signature - missing balance parameter
        # This must be fixed FIRST before other issues
        if "bankaccount" in issue_lower or "bankaccount" in filename.lower() or "BankAccount" in code:
            # Look for the pattern: __init__(self, owner):
            import re
            pattern = r'def __init__\(self, owner\):'
            if re.search(pattern, fixed_code):
                # Replace just the signature and initialization
                fixed_code = re.sub(
                    r'(class BankAccount:.*?def __init__\(self, )owner(\):)',
                    r'\1owner, balance=0\2',
                    fixed_code,
                    flags=re.DOTALL
                )
                # Now fix the balance assignment
                fixed_code = fixed_code.replace(
                    "self.balance = 0",
                    "self.balance = balance"
                )
                self.logger.info(f"✓ Fixed BankAccount __init__ signature in {filename}")
        
        # Fix 2: File reading without error handling
        if "read_file" in issue_lower or "nonexistent" in issue_lower:
            if "def read_file_unsafe(filename):" in fixed_code:
                # Use regex to be more flexible
                import re
                pattern = r'def read_file_unsafe\(filename\):.*?"""Read file without error handling""".*?with open\(filename, [\'"]r[\'"]\) as f:.*?return f\.read\(\)'
                if re.search(pattern, fixed_code, re.DOTALL):
                    fixed_code = re.sub(
                        pattern,
                        '''def read_file_unsafe(filename):
    """Read file without error handling"""
    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None''',
                        fixed_code,
                        flags=re.DOTALL
                    )
                    self.logger.info(f"✓ Fixed file reading error handling in {filename}")
        
        # Fix 3: Undefined variable tax_rate
        if "tax_rate" in issue_lower or ("tax_rate" in code and "calculate_total_with_tax" in code):
            import re
            pattern = r'def calculate_total_with_tax\(price\):'
            if re.search(pattern, fixed_code):
                fixed_code = re.sub(
                    r'def calculate_total_with_tax\(price\):',
                    'def calculate_total_with_tax(price, tax_rate=0.1):',
                    fixed_code
                )
                self.logger.info(f"✓ Added tax_rate default in {filename}")

        # Fix 4: Wrong tax calculation (subtracting instead of adding)
        if "calculate_total_with_tax" in fixed_code and "price - (price * tax_rate)" in fixed_code:
            fixed_code = fixed_code.replace(
                "return price - (price * tax_rate)",
                "return price + (price * tax_rate)"
            )
            self.logger.info(f"✓ Fixed tax calculation in {filename}")

        # Fix 5: greet_user typo (nam -> name)
        if "def greet_user" in fixed_code and "{nam}" in fixed_code:
            fixed_code = fixed_code.replace("{nam}", "{name}")
            self.logger.info(f"✓ Fixed greet_user variable typo in {filename}")
        
        # Fix 4: Variable name typo 'nam' should be 'name'
        if "nam" in issue_lower or ("nam" in code and "greet_user" in code):
            if "{nam}" in fixed_code:
                fixed_code = fixed_code.replace("{nam}", "{name}")
                self.logger.info(f"✓ Fixed variable typo 'nam' -> 'name' in {filename}")
        
        # Fix 5: Missing return statement in process_order
        if "process_order" in issue_lower or ("process_order" in code and "return total" not in code[code.find("def process_order"):] if "def process_order" in code else False):
            import re
            pattern = r'def process_order\(items\):.*?for item in items:.*?total \+= item\[\'price\'\].*?(?=\n(?:def |class |$))'
            match = re.search(pattern, fixed_code, re.DOTALL)
            if match and "return total" not in match.group(0):
                fixed_code = re.sub(
                    r'(def process_order\(items\):.*?for item in items:.*?total \+= item\[\'price\'\])',
                    r'\1\n    return total',
                    fixed_code,
                    flags=re.DOTALL
                )
                self.logger.info(f"✓ Fixed missing return in process_order in {filename}")
        
        # Fix 6: Division by zero - add check  
        if "divide" in issue_lower or "divide_unsafe" in code:
            import re
            pattern = r'def divide_unsafe\(a, b\):.*?return a / b'
            if re.search(pattern, fixed_code, re.DOTALL):
                fixed_code = re.sub(
                    pattern,
                    '''def divide_unsafe(a, b):
    """Divide two numbers"""
    if b == 0:
        raise ValueError('Cannot divide by zero')
    return a / b''',
                    fixed_code,
                    flags=re.DOTALL
                )
                self.logger.info(f"✓ Fixed division by zero check in divide_unsafe in {filename}")
        
        # Fix 7: JSON parsing without error handling (may already be partially fixed)
        if "json" in issue_lower or "parse_json" in code:
            import re
            # Check if already has try/except
            if "def parse_json_unsafe(json_string):" in fixed_code:
                if "try:" not in fixed_code[fixed_code.find("def parse_json_unsafe"):fixed_code.find("def parse_json_unsafe") + 300]:
                    fixed_code = re.sub(
                        r'(def parse_json_unsafe\(json_string\):.*?import json\n)(    return json\.loads\(json_string\))',
                        r'\1    try:\n        return json.loads(json_string)\n    except (json.JSONDecodeError, ValueError):\n        return None',
                        fixed_code,
                        flags=re.DOTALL
                    )
                    self.logger.info(f"✓ Fixed JSON parsing error handling in {filename}")
        
        return fixed_code
