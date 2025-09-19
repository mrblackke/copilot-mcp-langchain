"""
Parallel execution strategy.

This strategy enables concurrent execution of multiple pipeline steps
with proper synchronization and error handling.
"""

import asyncio
import logging
from typing import Any, Dict

from .base import ExecutionStrategy
from ..models import PipelineResult, ExecutionContext

logger = logging.getLogger('mcp_server.pipeline.strategies.parallel')


class ParallelStrategy(ExecutionStrategy):
    """Strategy for parallel execution of multiple steps."""
    
    def can_handle(self, step: Dict[str, Any]) -> bool:
        """Handle parallel execution steps."""
        return (
            step.get("type") == "parallel" or
            "parallel" in step
        )
    
    async def execute(self, step: Dict[str, Any], context: ExecutionContext, executor) -> PipelineResult:
        """Execute multiple steps in parallel."""
        try:
            parallel_steps = step.get("parallel", step.get("steps", []))
            max_concurrent = step.get("maxConcurrent", 10)
            
            if not parallel_steps:
                return PipelineResult(
                    success=False,
                    error=f"Step {context.step_number}: parallel requires steps to execute",
                    step=context.step_number,
                    context=context.variables
                )
            
            logger.info(f"Step {context.step_number}: Executing {len(parallel_steps)} steps in parallel")
            
            # Create semaphore for concurrent limit
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def execute_step_with_semaphore(step_data, step_index):
                async with semaphore:
                    # Create separate context for each parallel step
                    parallel_context = ExecutionContext(
                        variables=context.variables.copy(),
                        step_number=f"{context.step_number}.{step_index + 1}"
                    )
                    return await executor._execute_step(step_data, parallel_context)
            
            # Execute all steps concurrently
            tasks = [
                execute_step_with_semaphore(step_data, i)
                for i, step_data in enumerate(parallel_steps)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            all_success = True
            error_messages = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    all_success = False
                    error_messages.append(f"Parallel step {i+1}: {str(result)}")
                elif not result.success:
                    all_success = False
                    error_messages.append(f"Parallel step {i+1}: {result.error}")
                else:
                    # Merge successful results back to main context
                    context.variables.update(result.context)
            
            if not all_success:
                return PipelineResult(
                    success=False,
                    error=f"Step {context.step_number} parallel execution failed: {'; '.join(error_messages)}",
                    step=context.step_number,
                    context=context.variables
                )
            
            return PipelineResult(success=True, context=context.variables)
            
        except Exception as e:
            error_msg = f"Step {context.step_number} parallel execution failed: {str(e)}"
            logger.error(error_msg)
            return PipelineResult(
                success=False,
                error=error_msg,
                step=context.step_number,
                context=context.variables
            )
    
    @property
    def strategy_name(self) -> str:
        return "Parallel"
