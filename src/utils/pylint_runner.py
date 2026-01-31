"""
Pylint Runner Utility
Executes pylint analysis on Python files and captures results.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List


class PylintRunner:
    """Utility for running pylint and parsing results."""

    def __init__(self, target_dir: str):
        """
        Initialize pylint runner with target directory.
        
        Args:
            target_dir: Path to directory containing code to analyze
        """
        self.target_dir = Path(target_dir)

    def run_pylint(self, relative_path: str) -> Dict:
        """
        Run pylint on a specific Python file.
        
        Args:
            relative_path: Path relative to target_dir
            
        Returns:
            Dict with keys:
                - success (bool): Whether pylint ran successfully
                - score (float): Pylint score (0-10)
                - messages (list): List of issues found
                - raw_output (str): Full pylint output
        """
        file_path = self.target_dir / relative_path
        
        if not file_path.exists():
            return {
                "success": False,
                "score": 0,
                "messages": [f"File not found: {relative_path}"],
                "raw_output": ""
            }

        try:
            # First run: Get JSON output for detailed messages
            result_json = subprocess.run(
                ["python", "-m", "pylint", str(file_path), "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse JSON output
            if result_json.stdout:
                try:
                    messages = json.loads(result_json.stdout)
                except json.JSONDecodeError:
                    messages = []
            else:
                messages = []
            
            # Second run: Get text output to extract score
            result_text = subprocess.run(
                ["python", "-m", "pylint", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Extract score from text output
            score = 0.0
            output = result_text.stdout + result_text.stderr
            
            if "Your code has been rated at" in output:
                # Extract score like "8.5/10"
                parts = output.split("Your code has been rated at ")
                if len(parts) > 1:
                    score_str = parts[1].split("/")[0].strip()
                    try:
                        score = float(score_str)
                    except ValueError:
                        pass
            
            return {
                "success": True,
                "score": score,
                "messages": messages,
                "raw_output": output
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "score": 0,
                "messages": ["Pylint execution timed out"],
                "raw_output": ""
            }
        except Exception as e:
            return {
                "success": False,
                "score": 0,
                "messages": [str(e)],
                "raw_output": ""
            }

    def run_on_directory(self, py_files: List[str]) -> Dict[str, Dict]:
        """
        Run pylint on multiple Python files.
        
        Args:
            py_files: List of relative paths to analyze
            
        Returns:
            Dict mapping filepath -> pylint results
        """
        results = {}
        for py_file in py_files:
            results[py_file] = self.run_pylint(py_file)
        return results

    def summarize_results(self, results: Dict[str, Dict]) -> Dict:
        """
        Summarize pylint results across multiple files.
        
        Args:
            results: Output from run_on_directory()
            
        Returns:
            Dict with summary statistics
        """
        scores = [r["score"] for r in results.values() if r["success"]]
        all_messages = []
        
        for r in results.values():
            all_messages.extend(r["messages"])
        
        return {
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "total_issues": len(all_messages),
            "files_analyzed": len([r for r in results.values() if r["success"]]),
            "files_failed": len([r for r in results.values() if not r["success"]])
        }
