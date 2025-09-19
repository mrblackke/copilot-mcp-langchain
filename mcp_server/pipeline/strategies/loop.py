"""
Loop execution strategy.

This strategy handles various types of loops: forEach, while, and repeat.
Supports complex expressions and maintains proper variable scoping.
"""

import logging
from typing import Any, Dict

from .base import ExecutionStrategy
from ..models import PipelineResult, ExecutionContext
from ..expressions import substitute_in_object, parse_substituted_string

logger = logging.getLogger('mcp_server.pipeline.strategies.loop')


class LoopStrategy(ExecutionStrategy):
    """Strategy for handling loops (forEach, while, repeat)."""
    
    def __init__(self):
        pass
    
    def can_handle(self, step: Dict[str, Any]) -> bool:
        """Handle loop-related steps."""
        return (
            step.get("type") in ["loop", "forEach", "while", "repeat"] or
            "forEach" in step or
            "while" in step or
            "repeat" in step
        )
    
    async def execute(self, step: Dict[str, Any], context: ExecutionContext, executor) -> PipelineResult:
        """Execute different types of loops."""
        try:
            loop_type = step.get("type", "forEach")
            
            if "forEach" in step or loop_type == "forEach":
                return await self._execute_for_each(step, context, executor)
            elif "while" in step or loop_type == "while":
                return await self._execute_while(step, context, executor)
            elif "repeat" in step or loop_type == "repeat":
                return await self._execute_repeat(step, context, executor)
            else:
                return PipelineResult(
                    success=False,
                    error=f"Step {context.step_number}: unknown loop type '{loop_type}'",
                    step=context.step_number,
                    context=context.variables
                )
                
        except Exception as e:
            error_msg = f"Step {context.step_number} loop failed: {str(e)}"
            logger.error(error_msg)
            return PipelineResult(
                success=False,
                error=error_msg,
                step=context.step_number,
                context=context.variables
            )
    
    async def _execute_for_each(self, step: Dict[str, Any], context: ExecutionContext, executor) -> PipelineResult:
        """Execute forEach loop over collection."""
        collection_expr = step.get("forEach", step.get("collection", ""))
        item_var = step.get("item", "item")
        index_var = step.get("index", "index")
        body_steps = step.get("do", step.get("body", []))
        item_output_expr = step.get("item_output")  
        output_var = step.get("output") 
        
        if not collection_expr:
            return PipelineResult(
                success=False,
                error=f"Step {context.step_number}: forEach requires collection expression",
                step=context.step_number,
                context=context.variables
            )
        
        # Get collection from variables - handle all expression types
        try:
            logger.info(f"DEBUG: forEach expression: '{collection_expr}', context keys: {list(context.variables.keys())}")
            
            # Подставляем выражения через единую точку (результат - строка)
            substituted_expr = substitute_in_object(collection_expr, context.variables)
            logger.info(f"DEBUG: forEach after substitution: {substituted_expr!r}")
            
            # Интерпретируем строку как Python объект для forEach
            collection = parse_substituted_string(substituted_expr, context.variables)
            logger.info(f"DEBUG: forEach parsed collection: {type(collection)} = {collection}")
            
        except Exception as e:
            logger.error(f"DEBUG: forEach expression evaluation error: {str(e)}")
            return PipelineResult(
                success=False,
                error=f"Step {context.step_number}: forEach collection evaluation failed: {str(e)}",
                step=context.step_number,
                context=context.variables
            )
        
        if not isinstance(collection, (list, tuple)):
            return PipelineResult(
                success=False,
                error=f"Step {context.step_number}: forEach collection must be a list, got {type(collection)}",
                step=context.step_number,
                context=context.variables
            )
        
        logger.info(f"Step {context.step_number}: ForEach loop over {len(collection)} items")
        
        # Initialize accumulator for results if item_output is specified
        accumulated_results = [] if item_output_expr else None
        
        # Execute body for each item
        for i, item in enumerate(collection):
            # Set loop variables
            original_item = context.variables.get(item_var)
            original_index = context.variables.get(index_var)
            
            context.variables[item_var] = item
            context.variables[index_var] = i
            
            try:
                # Execute body steps
                result = await executor._execute_sub_pipeline(body_steps, context, f"LOOP[{i}]")
                if not result.success:
                    return result
                
                # If item_output is specified, evaluate and accumulate
                if item_output_expr and accumulated_results is not None:
                    try:
                        # Подставляем выражения и парсим результат
                        substituted_result = substitute_in_object(item_output_expr, context.variables)
                        item_result = parse_substituted_string(substituted_result, context.variables)
                        accumulated_results.append(item_result)
                        logger.debug(f"ForEach iteration {i}: accumulated item result: {str(item_result)[:1000] + '...' if len(str(item_result)) > 1000 else item_result}")
                    except Exception as e:
                        logger.warning(f"ForEach iteration {i}: failed to evaluate item_output: {str(e)}")
                        
            finally:
                # Restore original variables
                if original_item is not None:
                    context.variables[item_var] = original_item
                else:
                    context.variables.pop(item_var, None)
                
                if original_index is not None:
                    context.variables[index_var] = original_index
                else:
                    context.variables.pop(index_var, None)
        
        # Store accumulated results if specified
        if item_output_expr and output_var and accumulated_results is not None:
            context.variables[output_var] = accumulated_results
            logger.info(f"ForEach completed: accumulated {len(accumulated_results)} results in '{output_var}'")
        
        return PipelineResult(success=True, context=context.variables)
    
    async def _execute_while(self, step: Dict[str, Any], context: ExecutionContext, executor) -> PipelineResult:
        """Execute while loop with condition."""
        condition_expr = step.get("while", step.get("condition", ""))
        body_steps = step.get("do", step.get("body", []))
        max_iterations = step.get("maxIterations", 1000)  # Safety limit
        
        if not condition_expr:
            return PipelineResult(
                success=False,
                error=f"Step {context.step_number}: while requires condition expression",
                step=context.step_number,
                context=context.variables
            )
        
        logger.info(f"Step {context.step_number}: While loop with condition: {condition_expr}")
        
        iteration = 0
        while iteration < max_iterations:
            # Check condition
            try:
                # Подставляем выражения и парсим результат как Python объект
                substituted_condition = substitute_in_object(condition_expr, context.variables)
                condition_result = parse_substituted_string(substituted_condition, context.variables)
                if not condition_result:
                    break
            except Exception as e:
                return PipelineResult(
                    success=False,
                    error=f"Step {context.step_number}: while condition failed: {str(e)}",
                    step=context.step_number,
                    context=context.variables
                )
            
            # Execute body
            result = await executor._execute_sub_pipeline(body_steps, context, f"WHILE[{iteration}]")
            if not result.success:
                return result
            
            iteration += 1
        
        if iteration >= max_iterations:
            logger.warning(f"Step {context.step_number}: While loop reached max iterations ({max_iterations})")
        
        return PipelineResult(success=True, context=context.variables)
    
    async def _execute_repeat(self, step: Dict[str, Any], context: ExecutionContext, executor) -> PipelineResult:
        """Execute repeat loop with fixed count."""
        count_expr = step.get("repeat", step.get("count", ""))
        body_steps = step.get("do", step.get("body", []))
        counter_var = step.get("counter", "counter")
        
        if not count_expr:
            return PipelineResult(
                success=False,
                error=f"Step {context.step_number}: repeat requires count expression",
                step=context.step_number,
                context=context.variables
            )
        
        # Get repeat count - handle both numbers and expressions
        try:
            if isinstance(count_expr, (int, float)):
                count = int(count_expr)
            else:
                # Подставляем выражения и парсим результат
                substituted_count = substitute_in_object(str(count_expr), context.variables)
                evaluated = parse_substituted_string(substituted_count, context.variables)
                count = int(evaluated)
        except Exception as e:
            return PipelineResult(
                success=False,
                error=f"Step {context.step_number}: repeat count evaluation failed: {str(e)}",
                step=context.step_number,
                context=context.variables
            )
        
        if not isinstance(count, int) or count < 0:
            return PipelineResult(
                success=False,
                error=f"Step {context.step_number}: repeat count must be a non-negative integer, got {count}",
                step=context.step_number,
                context=context.variables
            )
        
        logger.info(f"Step {context.step_number}: Repeat loop {count} times")
        
        # Execute body for each iteration
        original_counter = context.variables.get(counter_var)
        
        try:
            for i in range(count):
                context.variables[counter_var] = i
                
                result = await executor._execute_sub_pipeline(body_steps, context, f"REPEAT[{i}]")
                if not result.success:
                    return result
        finally:
            # Restore original counter
            if original_counter is not None:
                context.variables[counter_var] = original_counter
            else:
                context.variables.pop(counter_var, None)
        
        return PipelineResult(success=True, context=context.variables)
    
    @property
    def strategy_name(self) -> str:
        return "Loop"
