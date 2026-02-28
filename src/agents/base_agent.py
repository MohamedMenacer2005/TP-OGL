"""
Base Agent Template
Provides abstract interface and auto-logging for all refactoring agents.
"""

from abc import ABC, abstractmethod
import logging
from src.utils.logger import log_experiment, ActionType
from src.utils.prompt_manager import PromptManager


class BaseAgent(ABC):
    """
    Abstract base class for all refactoring agents.
    Handles logging automatically; child agents focus on analysis/generation logic.
    """

    def __init__(self, agent_name: str, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize agent.
        
        Args:
            agent_name: Unique identifier for this agent (e.g., "CodeAuditor", "Refactorer")
            model: LLM model to use (default: models/gemini-2.5-flash)
        """
        self.agent_name = agent_name
        self.model = model
        self.logger = logging.getLogger(agent_name)
        self.prompt_manager = PromptManager()

    def _log_action(self, action: ActionType, prompt: str, response: str, 
                    extra_details: dict = None, status: str = "SUCCESS") -> None:
        """
        Log an agent action with automatic prompt/response capture.
        
        Args:
            action: ActionType enum value (ANALYSIS, GENERATION, DEBUG, FIX)
            prompt: Input prompt sent to LLM
            response: LLM response received
            extra_details: Optional additional fields to log (e.g., target_file, issues_found)
            status: "SUCCESS" or "FAILURE"
        """
        details = {
            "input_prompt": prompt,
            "output_response": response
        }
        
        # Merge extra details if provided
        if extra_details:
            details.update(extra_details)
        
        log_experiment(
            agent_name=self.agent_name,
            model_used=self.model,
            action=action,
            details=details,
            status=status
        )

    @abstractmethod
    def analyze(self, code: str, filename: str = "unknown.py") -> dict:
        """
        Analyze code and return findings.
        
        Args:
            code: Python code to analyze
            filename: Optional filename for context
            
        Returns:
            Dict with analysis results (structure defined by subclass)
        """
        pass

    @abstractmethod
    def execute(self, target_dir: str) -> dict:
        """
        Execute agent's main task on target directory.
        
        Args:
            target_dir: Path to code directory
            
        Returns:
            Dict with execution results
        """
        pass


# Example: Simple analyzer agent (for Phase 1 testing)
class SimpleAnalyzer(BaseAgent):
    """
    Minimal analyzer that reads a file and logs it.
    Used for testing Phase 1 infrastructure.
    """

    def analyze(self, code: str, filename: str = "unknown.py") -> dict:
        """Log that code was read (no actual analysis yet)."""
        preview = code[:500]
        prompt = self.prompt_manager.format("simple_analyzer_review", preview=preview)
        response = f"Code file '{filename}' has {len(code)} characters. Analysis would go here."
        
        self._log_action(
            action=ActionType.ANALYSIS,
            prompt=prompt,
            response=response,
            extra_details={"filename": filename, "code_length": len(code)}
        )
        
        return {
            "filename": filename,
            "code_length": len(code),
            "status": "analyzed"
        }

    def execute(self, target_dir: str) -> dict:
        """Execute analysis on all files in target directory."""
        from src.utils.code_reader import CodeReader
        
        reader = CodeReader(target_dir)
        files = reader.read_all_python_files()
        
        results = {}
        for filename, content in files.items():
            results[filename] = self.analyze(content, filename)
        
        return {
            "agent": self.agent_name,
            "files_analyzed": len(results),
            "results": results
        }
