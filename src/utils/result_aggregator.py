"""
Result Aggregator Utility
Collect and merge agent outputs into structured result objects.
Toolsmith data structure for passing iteration results.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class AgentOutput:
    """Output from a single agent execution."""
    agent_name: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    success: bool = True
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_seconds: float = 0.0


@dataclass
class IterationResult:
    """Result of a complete iteration (Auditor → Fixer → Judge)."""
    iteration_num: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    auditor_output: Optional[AgentOutput] = None
    fixer_output: Optional[AgentOutput] = None
    judge_output: Optional[AgentOutput] = None
    judge_decision: Optional[str] = None  # "ACCEPT", "REJECT", or None
    target_file: Optional[str] = None


class ResultAggregator:
    """
    Collects and merges results from multiple agents.
    Provides structured access to iteration data.
    """
    
    def __init__(self):
        """Initialize aggregator."""
        self.results: List[IterationResult] = []
        self.current_iteration = 0
    
    def create_iteration(self, iteration_num: int, target_file: str = None) -> IterationResult:
        """
        Create a new iteration result.
        
        Args:
            iteration_num: Iteration number
            target_file: Optional target file being analyzed
            
        Returns:
            New IterationResult object
        """
        result = IterationResult(
            iteration_num=iteration_num,
            target_file=target_file
        )
        self.results.append(result)
        self.current_iteration = iteration_num
        return result
    
    def add_auditor_output(
        self,
        iteration_num: int,
        output: Dict[str, Any],
        success: bool = True,
        error: str = None,
        execution_time: float = 0.0
    ) -> None:
        """
        Add auditor output to iteration result.
        
        Args:
            iteration_num: Iteration number
            output: Auditor output dict
            success: Whether execution succeeded
            error: Error message if failed
            execution_time: Execution time in seconds
        """
        result = self._get_or_create_iteration(iteration_num)
        result.auditor_output = AgentOutput(
            agent_name="Auditor",
            success=success,
            output=output,
            error=error,
            execution_time_seconds=execution_time
        )
    
    def add_fixer_output(
        self,
        iteration_num: int,
        output: Dict[str, Any],
        success: bool = True,
        error: str = None,
        execution_time: float = 0.0
    ) -> None:
        """Add fixer output to iteration result."""
        result = self._get_or_create_iteration(iteration_num)
        result.fixer_output = AgentOutput(
            agent_name="Fixer",
            success=success,
            output=output,
            error=error,
            execution_time_seconds=execution_time
        )
    
    def add_judge_output(
        self,
        iteration_num: int,
        output: Dict[str, Any],
        decision: str,
        success: bool = True,
        error: str = None,
        execution_time: float = 0.0
    ) -> None:
        """
        Add judge output to iteration result.
        
        Args:
            iteration_num: Iteration number
            output: Judge output dict
            decision: Judge decision ("ACCEPT", "REJECT", etc.)
            success: Whether execution succeeded
            error: Error message if failed
            execution_time: Execution time in seconds
        """
        result = self._get_or_create_iteration(iteration_num)
        result.judge_output = AgentOutput(
            agent_name="Judge",
            success=success,
            output=output,
            error=error,
            execution_time_seconds=execution_time
        )
        result.judge_decision = decision
    
    def get_iteration(self, iteration_num: int) -> Optional[IterationResult]:
        """Get result for specific iteration."""
        for result in self.results:
            if result.iteration_num == iteration_num:
                return result
        return None
    
    def get_last_iteration(self) -> Optional[IterationResult]:
        """Get most recent iteration."""
        return self.results[-1] if self.results else None
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Generate summary of all iterations.
        
        Returns:
            Dict with statistics and history
        """
        if not self.results:
            return {
                "total_iterations": 0,
                "accepted": 0,
                "rejected": 0,
                "failed": 0,
                "iterations": []
            }
        
        accepted = sum(1 for r in self.results if r.judge_decision == "ACCEPT")
        rejected = sum(1 for r in self.results if r.judge_decision == "REJECT")
        failed = sum(1 for r in self.results if r.judge_output and not r.judge_output.success)
        
        total_time = sum(
            (r.auditor_output.execution_time_seconds if r.auditor_output else 0) +
            (r.fixer_output.execution_time_seconds if r.fixer_output else 0) +
            (r.judge_output.execution_time_seconds if r.judge_output else 0)
            for r in self.results
        )
        
        return {
            "total_iterations": len(self.results),
            "accepted": accepted,
            "rejected": rejected,
            "failed": failed,
            "total_execution_time": round(total_time, 2),
            "iterations": [self._iteration_to_dict(r) for r in self.results]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert all results to dictionary (for JSON serialization)."""
        return {
            "total_iterations": len(self.results),
            "iterations": [self._iteration_to_dict(r) for r in self.results]
        }
    
    def _get_or_create_iteration(self, iteration_num: int) -> IterationResult:
        """Get iteration result, creating if needed."""
        result = self.get_iteration(iteration_num)
        if not result:
            result = self.create_iteration(iteration_num)
        return result
    
    @staticmethod
    def _iteration_to_dict(result: IterationResult) -> Dict[str, Any]:
        """Convert iteration result to dict."""
        return {
            "iteration_num": result.iteration_num,
            "timestamp": result.timestamp,
            "target_file": result.target_file,
            "auditor": asdict(result.auditor_output) if result.auditor_output else None,
            "fixer": asdict(result.fixer_output) if result.fixer_output else None,
            "judge": asdict(result.judge_output) if result.judge_output else None,
            "judge_decision": result.judge_decision
        }


class ResultBuilder:
    """Fluent builder for creating iteration results."""
    
    def __init__(self, iteration_num: int):
        """Initialize builder."""
        self.result = IterationResult(iteration_num=iteration_num)
    
    def with_auditor(self, output: Dict, success: bool = True, error: str = None) -> 'ResultBuilder':
        """Add auditor output."""
        self.result.auditor_output = AgentOutput(
            agent_name="Auditor",
            success=success,
            output=output,
            error=error
        )
        return self
    
    def with_fixer(self, output: Dict, success: bool = True, error: str = None) -> 'ResultBuilder':
        """Add fixer output."""
        self.result.fixer_output = AgentOutput(
            agent_name="Fixer",
            success=success,
            output=output,
            error=error
        )
        return self
    
    def with_judge(self, output: Dict, decision: str, success: bool = True, error: str = None) -> 'ResultBuilder':
        """Add judge output."""
        self.result.judge_output = AgentOutput(
            agent_name="Judge",
            success=success,
            output=output,
            error=error
        )
        self.result.judge_decision = decision
        return self
    
    def with_target_file(self, filename: str) -> 'ResultBuilder':
        """Set target file."""
        self.result.target_file = filename
        return self
    
    def build(self) -> IterationResult:
        """Build final result."""
        return self.result
