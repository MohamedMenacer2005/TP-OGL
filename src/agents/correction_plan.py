"""
Correction Plan data structure for tracking code refactoring results.
"""

from typing import Dict, List


class CorrectionPlan:
    """
    Structured correction plan from CorrectorAgent.
    
    Provides convenient access to correction results and analysis methods.
    """
    
    def __init__(self, result: Dict = None):
        """
        Initialize correction plan.
        
        Args:
            result: Dictionary with correction results
        """
        self.result = result or {}
        self.corrections = self.result.get("corrections", {})
    
    def get_refactored_files(self) -> List[str]:
        """
        Get list of files that have corrections.
        
        Returns:
            List of filenames with successful corrections
        """
        return [
            filename 
            for filename, data in self.corrections.items() 
            if data.get("status") == "corrected" and data.get("corrections_count", 0) > 0
        ]
    
    def get_total_changes(self) -> int:
        """
        Get total number of corrections generated.
        
        Returns:
            Total correction count
        """
        return self.result.get("total_corrections", 0)
    
    def get_corrections_by_file(self) -> Dict[str, List[str]]:
        """
        Map files to their corrections.
        
        Returns:
            Dict mapping filenames to lists of issues corrected
        """
        result = {}
        
        for filename, data in self.corrections.items():
            if data.get("status") == "corrected" and "corrections" in data:
                issues = [c.get("issue", "unknown") for c in data["corrections"]]
                result[filename] = issues
        
        return result
    
    def get_files_with_errors(self) -> List[str]:
        """
        Get list of files that failed correction.
        
        Returns:
            List of filenames with errors
        """
        return [
            filename 
            for filename, data in self.corrections.items() 
            if data.get("status") == "error"
        ]
    
    def get_total_lines_changed(self) -> int:
        """
        Calculate total lines changed across all corrections.
        
        Returns:
            Total line count changed
        """
        total = 0
        
        for data in self.corrections.values():
            if data.get("status") == "corrected":
                for correction in data.get("corrections", []):
                    total += correction.get("lines_changed", 0)
        
        return total
    
    def to_dict(self) -> Dict:
        """
        Convert to dict for JSON serialization.
        
        Returns:
            Dictionary representation of plan
        """
        return {
            "files_corrected": self.result.get("files_corrected", 0),
            "total_corrections": self.get_total_changes(),
            "total_lines_changed": self.get_total_lines_changed(),
            "corrections_by_file": self.get_corrections_by_file(),
            "refactored_files": self.get_refactored_files(),
            "error_files": self.get_files_with_errors(),
            "ready_for_review": len(self.get_refactored_files()) > 0
        }
    
    def __str__(self) -> str:
        """String representation of plan."""
        return (
            f"CorrectionPlan(files={self.result.get('files_corrected', 0)}, "
            f"corrections={self.get_total_changes()}, "
            f"lines_changed={self.get_total_lines_changed()})"
        )
