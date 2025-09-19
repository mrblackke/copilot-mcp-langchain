"""
Delay execution strategy.

This strategy handles timing operations like delays, sleeps, and waits
with support for dynamic duration expressions.
"""

import asyncio
import logging
from typing import Any, Dict

from .base import ExecutionStrategy
from ..models import PipelineResult, ExecutionContext
from ..expressions import evaluate_expression

logger = logging.getLogger('mcp_server.pipeline.strategies.delay')


class DelayStrategy(ExecutionStrategy):
    """Strategy for delays and timing control."""
    
    def __init__(self):
        pass
    
    def can_handle(self, step: Dict[str, Any]) -> bool:
        """Handle delay and timing steps."""
        return (
            step.get("type") == "delay" or
            "delay" in step or
            "sleep" in step or
            "wait" in step
        )
    
    async def execute(self, step: Dict[str, Any], context: ExecutionContext, executor) -> PipelineResult:
        """Execute delay/sleep operation."""
        try:
            # Get delay duration from various possible fields
            delay_value = (
                step.get("delay") or
                step.get("sleep") or
                step.get("wait") or
                step.get("duration", 0)
            )
            
            if isinstance(delay_value, str):
                # Evaluate expression for dynamic delays
                delay_seconds = float(evaluate_expression(delay_value, context.variables, expected_result_type="python"))
            else:
                delay_seconds = float(delay_value)
            
            if delay_seconds < 0:
                return PipelineResult(
                    success=False,
                    error=f"Step {context.step_number}: delay cannot be negative: {delay_seconds}",
                    step=context.step_number,
                    context=context.variables
                )
            
            logger.info(f"Step {context.step_number}: Delaying for {delay_seconds} seconds")
            
            await asyncio.sleep(delay_seconds)
            
            return PipelineResult(success=True, context=context.variables)
            
        except Exception as e:
            error_msg = f"Step {context.step_number} delay failed: {str(e)}"
            logger.error(error_msg)
            return PipelineResult(
                success=False,
                error=error_msg,
                step=context.step_number,
                context=context.variables
            )
    
    @property
    def strategy_name(self) -> str:
        return "Delay"
