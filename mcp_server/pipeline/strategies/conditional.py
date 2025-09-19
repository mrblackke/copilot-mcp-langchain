"""
Conditional execution strategy.

This strategy handles if-then-else logic with JavaScript-like expression evaluation
for conditions. Supports complex boolean expressions and nested pipeline execution.
"""

import logging
from typing import Any, Dict

from .base import ExecutionStrategy
from ..models import PipelineResult, ExecutionContext
from ..expressions import evaluate_expression

logger = logging.getLogger('mcp_server.pipeline.strategies.conditional')


class ConditionalStrategy(ExecutionStrategy):
    """Strategy for handling conditional logic (if-then-else)."""
    
    def __init__(self):
        pass
    
    def can_handle(self, step: Dict[str, Any]) -> bool:
        """Handle steps with conditional logic."""
        return (
            step.get("type") == "condition" or
            "condition" in step or
            "if" in step
        )
    
    async def execute(self, step: Dict[str, Any], context: ExecutionContext, executor) -> PipelineResult:
        """Execute conditional logic with then/else branches."""
        try:
            # Support multiple condition syntaxes
            condition_expr = (
                step.get("condition") or 
                step.get("if") or 
                ""
            )
            then_steps = step.get("then", [])
            else_steps = step.get("else", [])
            
            if not condition_expr:
                return PipelineResult(
                    success=False,
                    error=f"Step {context.step_number}: condition expression is required",
                    step=context.step_number,
                    context=context.variables
                )
            
            logger.info(f"Step {context.step_number}: Evaluating condition: {condition_expr}")
            
            # Evaluate condition using expression handler
            condition_result = self._evaluate_condition(condition_expr, context.variables)
            logger.info(f"Step {context.step_number}: Condition result: {condition_result}")
            
            # Execute appropriate branch
            if condition_result and then_steps:
                logger.info(f"Step {context.step_number}: Executing THEN block with {len(then_steps)} steps")
                return await executor._execute_sub_pipeline(then_steps, context, "THEN")
            elif not condition_result and else_steps:
                logger.info(f"Step {context.step_number}: Executing ELSE block with {len(else_steps)} steps")
                return await executor._execute_sub_pipeline(else_steps, context, "ELSE")
            else:
                logger.info(f"Step {context.step_number}: No applicable branch, skipping")
                return PipelineResult(success=True, context=context.variables)
                
        except Exception as e:
            error_msg = f"Step {context.step_number} condition failed: {str(e)}"
            logger.error(error_msg)
            return PipelineResult(
                success=False,
                error=error_msg,
                step=context.step_number,
                context=context.variables
            )
    
    def _evaluate_condition(self, condition: str, variables: Dict[str, Any]) -> bool:
        """Evaluate condition using JavaScript-like expressions."""
        try:
            # Direct evaluation using new expression system
            result = evaluate_expression(condition, variables, expected_result_type="python")
            
            # Convert to boolean using JavaScript-like truthiness
            if isinstance(result, bool):
                return result
            elif isinstance(result, (int, float)):
                return result != 0
            elif isinstance(result, str):
                return result.lower() not in ('false', '0', '', 'null', 'undefined')
            elif result is None:
                return False
            else:
                return bool(result)
                
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            raise
    
    @property
    def strategy_name(self) -> str:
        return "Conditional"
