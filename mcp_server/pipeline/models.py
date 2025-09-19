"""
Data models and types for pipeline execution.

This module contains all data classes, enums, and type definitions
used throughout the pipeline system.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum


@dataclass
class PipelineResult:
    """Result of pipeline execution."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    step: Optional[int] = None
    tool: Optional[str] = None
    context: Dict[str, Any] = None
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "step": self.step,
            "tool": self.tool,
            "context": self.context or {},
            "execution_time": self.execution_time
        }


@dataclass
class ExecutionContext:
    """Execution context for pipeline."""
    variables: Dict[str, Any]
    step_number: int = 0
    templates: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.templates is None:
            self.templates = {}


class StepType(Enum):
    """Pipeline step types (legacy - not used in strategy architecture)."""
    TOOL = "tool"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    TEMPLATE = "template"


# Export all models
__all__ = [
    'PipelineResult',
    'ExecutionContext',
    'StepType'
]
