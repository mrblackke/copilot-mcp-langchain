"""
Strategy-based pipeline execution system.

This module provides a modular, composition-based architecture for pipeline execution
with support for different step types through pluggable strategies.

Available strategies:
- ToolStrategy: Execute MCP tools with parameters
- ConditionalStrategy: If-then-else conditional logic
- LoopStrategy: For-each loops over arrays
- ParallelStrategy: Parallel execution of multiple steps
- DelayStrategy: Add delays between steps

Usage:
    from mcp_server.pipeline.strategies import StrategyBasedExecutor
    
    executor = StrategyBasedExecutor(tool_runner=run_tool)
    result = await executor.execute(pipeline_config)
"""

# Import base classes
from .base import ExecutionStrategy

# Import all strategy implementations
from .tool import ToolStrategy
from .conditional import ConditionalStrategy
from .loop import LoopStrategy
from .parallel import ParallelStrategy
from .delay import DelayStrategy

# Import main executor
from .executor import StrategyBasedExecutor

# Import core classes for backward compatibility
from ..models import ExecutionContext, PipelineResult

# Default alias for consistency with main module
PipelineExecutor = StrategyBasedExecutor

# Export all strategies and executor
__all__ = [
    # Main executor
    'StrategyBasedExecutor',
    'PipelineExecutor',  # Alias
    
    # Base class
    'ExecutionStrategy',
    
    # Strategy implementations
    'ToolStrategy',
    'ConditionalStrategy', 
    'LoopStrategy',
    'ParallelStrategy',
    'DelayStrategy',
    
    # Core classes for custom strategies
    'ExecutionContext',
    'PipelineResult'
]
