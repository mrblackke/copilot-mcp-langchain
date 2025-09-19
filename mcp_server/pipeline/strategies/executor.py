"""
Strategy-basefrom ..models import PipelineResult, ExecutionContext, StepType
from ..expressions import evaluate_expression, substitute_expressionsine executor.

This module contains the main executor that orchestrates all pipeline strategies
using composition pattern for maximum flexibility and extensibility.
"""

import time
import logging
from typing import Any, Dict, List, Callable

from .base import ExecutionStrategy
from .tool import ToolStrategy
from .conditional import ConditionalStrategy
from .loop import LoopStrategy
from .parallel import ParallelStrategy
from .delay import DelayStrategy

from ..models import PipelineResult, ExecutionContext, StepType
from ..expressions import evaluate_expression, substitute_expressions

logger = logging.getLogger('mcp_server.pipeline.strategies.executor')


class StrategyBasedExecutor:
    """
    Pipeline executor using strategy pattern for modular functionality.
    
    This executor uses composition instead of inheritance, allowing
    easy addition of new features through strategy plugins.
    
    Features:
    - ✅ Modular strategy system
    - ✅ Tool execution (basic functionality)
    - ✅ Conditional logic (if-then-else)
    - ✅ Loop support (forEach, while, repeat)
    - ✅ Parallel execution
    - ✅ Delay/timing control
    - 🚧 Template system (coming soon)
    - 🚧 Error handling strategies (coming soon)
    
    Usage:
        executor = StrategyBasedExecutor(tool_runner=run_tool)
        
        # Add custom strategies
        executor.add_strategy(CustomStrategy())
        
        result = await executor.execute(pipeline_config)
    """
    
    def __init__(self, tool_runner: Callable[[str, Dict[str, Any]], Any]):
        self.tool_runner = tool_runner
        
        # Initialize default strategies
        self.strategies: List[ExecutionStrategy] = []
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register all default execution strategies."""
        # Order matters: more specific strategies should come first
        self.add_strategy(ConditionalStrategy())
        self.add_strategy(LoopStrategy())
        self.add_strategy(ParallelStrategy())
        self.add_strategy(DelayStrategy())
        self.add_strategy(ToolStrategy(self.tool_runner))  # Fallback strategy
    
    def add_strategy(self, strategy: ExecutionStrategy):
        """Add a new execution strategy."""
        self.strategies.append(strategy)
        logger.info(f"Added strategy: {strategy.strategy_name}")
    
    def remove_strategy(self, strategy_name: str):
        """Remove a strategy by name."""
        self.strategies = [s for s in self.strategies if s.strategy_name != strategy_name]
        logger.info(f"Removed strategy: {strategy_name}")
    
    def get_strategies(self) -> List[str]:
        """Get list of registered strategy names."""
        return [s.strategy_name for s in self.strategies]
    
    async def execute(self, config: Dict[str, Any]) -> PipelineResult:
        """Execute a pipeline using the registered strategies."""
        start_time = time.time()
        
        try:
            # Initialize execution context
            context = ExecutionContext(variables={}, step_number=0)
            
            # Add user parameters to context if provided
            user_params = config.get("user_params", {})
            if user_params:
                context.variables["user"] = user_params
                logger.info(f"Added user parameters to context: {list(user_params.keys())}")
            
            pipeline = config.get("pipeline", [])
            final_result_expr = config.get("final_result", "ok")
            
            if not pipeline:
                # Empty pipeline is valid - just calculate final result
                logger.info("Empty pipeline provided, calculating final result only")
                try:
                    final_result = evaluate_expression(final_result_expr, context.variables, expected_result_type="python")
                except Exception as e:
                    logger.warning(f"Final result evaluation failed: {e}, using default")
                    final_result = "ok"
                
                execution_time = time.time() - start_time
                return PipelineResult(
                    success=True,
                    result=final_result,
                    context=context.variables,
                    execution_time=execution_time
                )
            
            logger.info(f"Starting pipeline execution with {len(pipeline)} steps")
            logger.info(f"Registered strategies: {', '.join(self.get_strategies())}")
            
            # Execute pipeline steps
            for i, step in enumerate(pipeline):
                context.step_number = i + 1
                
                result = await self._execute_step(step, context)
                if not result.success:
                    result.execution_time = time.time() - start_time
                    return result
            
            # Calculate final result
            try:
                final_result = evaluate_expression(final_result_expr, context.variables, expected_result_type="python")
            except Exception as e:
                logger.warning(f"Final result evaluation failed: {e}, using default")
                final_result = "ok"
            
            execution_time = time.time() - start_time
            logger.info(f"Pipeline completed successfully in {execution_time:.4f}s")
            
            return PipelineResult(
                success=True,
                result=final_result,
                context=context.variables,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Pipeline execution failed: {str(e)}"
            logger.error(error_msg)
            return PipelineResult(
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _execute_step(self, step: Dict[str, Any], context: ExecutionContext) -> PipelineResult:
        """Execute a single step using the appropriate strategy."""
        # Find strategy that can handle this step
        for strategy in self.strategies:
            if strategy.can_handle(step):
                logger.debug(f"Step {context.step_number}: Using {strategy.strategy_name} strategy")
                return await strategy.execute(step, context, self)
        
        # No strategy found
        return PipelineResult(
            success=False,
            error=f"Step {context.step_number}: No strategy found to handle step: {step}",
            step=context.step_number,
            context=context.variables
        )
    
    async def _execute_sub_pipeline(self, steps: List[Dict[str, Any]], context: ExecutionContext, block_type: str = "SUB") -> PipelineResult:
        """Execute a sub-pipeline (for conditional branches, loops, etc.)."""
        if not steps:
            return PipelineResult(success=True, context=context.variables)
        
        original_step = context.step_number
        
        try:
            for i, step in enumerate(steps):
                context.step_number = f"{original_step}.{i+1}"
                
                result = await self._execute_step(step, context)
                if not result.success:
                    return result
            
            context.step_number = original_step
            return PipelineResult(success=True, context=context.variables)
            
        except Exception as e:
            context.step_number = original_step
            error_msg = f"{block_type} sub-pipeline execution failed: {str(e)}"
            logger.error(error_msg)
            return PipelineResult(
                success=False,
                error=error_msg,
                step=context.step_number,
                context=context.variables
            )
