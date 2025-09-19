"""
Modern pipeline architecture for MCP tool chaining.

This module provides a comprehensive pipeline system with:
- Strategy-based architecture for extensibility  
- Support for conditionals, loops, parallel execution
- Advanced expression evaluation with ternary operators
- Clean separation of concerns

Usage:
    from mcp_server.pipeline import PipelineExecutor
    
    executor = PipelineExecutor(tool_runner=run_tool)
    result = await executor.execute(pipeline_config)
"""

# Import the main strategy-based executor
from .strategies import PipelineExecutor, StrategyBasedExecutor

# Import data models
from .models import PipelineResult, ExecutionContext, StepType

# Import expression evaluation functions
from .expressions import evaluate_expression, substitute_expressions

# Export clean public API
__all__ = [
    # Main executor (strategy-based)
    'PipelineExecutor',
    'StrategyBasedExecutor', 
    
    # Data models
    'PipelineResult',
    'ExecutionContext',
    'StepType',
    
    # Utility functions
    'evaluate_expression',
    'substitute_expressions'
]
