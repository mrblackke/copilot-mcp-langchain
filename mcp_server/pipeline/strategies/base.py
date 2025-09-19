"""
Base execution strategy interface.

This module defines the abstract base class for all pipeline execution strategies.
Each strategy implements specific functionality while following a common interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..models import PipelineResult, ExecutionContext


class ExecutionStrategy(ABC):
    """
    Base class for all pipeline execution strategies.
    
    Each strategy handles a specific type of pipeline step,
    enabling modular and extensible pipeline functionality.
    """
    
    @abstractmethod
    def can_handle(self, step: Dict[str, Any]) -> bool:
        """Check if this strategy can handle the given step."""
        pass
    
    @abstractmethod
    async def execute(self, step: Dict[str, Any], context: ExecutionContext, executor: 'StrategyBasedExecutor') -> PipelineResult:
        """Execute the step using this strategy."""
        pass
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Name of this strategy for logging and debugging."""
        pass


# Import StrategyBasedExecutor to avoid circular imports in type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .executor import StrategyBasedExecutor
