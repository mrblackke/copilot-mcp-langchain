"""
Tool execution strategy.

This strategy handles basic tool execution with parameter substitution
and result storage. It's the fundamental building block of the pipeline system.
"""

import asyncio
import logging
from typing import Any, Dict, Callable

from .base import ExecutionStrategy
from ..models import PipelineResult, ExecutionContext
from ..expressions import substitute_in_object, parse_substituted_string

logger = logging.getLogger('mcp_server.pipeline.strategies.tool')


class ToolStrategy(ExecutionStrategy):
    """Strategy for executing tool calls - the basic pipeline functionality."""
    
    def __init__(self, tool_runner: Callable[[str, Dict[str, Any]], Any]):
        self.tool_runner = tool_runner
    
    def can_handle(self, step: Dict[str, Any]) -> bool:
        """Handle steps that have a 'tool' field."""
        return "tool" in step and step.get("type", "tool") == "tool"
    
    async def execute(self, step: Dict[str, Any], context: ExecutionContext, executor) -> PipelineResult:
        """Execute a tool call with parameter substitution."""
        try:
            tool_name = step["tool"]
            params = step.get("params", {})
            output_var = step.get("output")
            
            logger.info(f"Step {context.step_number}: Executing tool '{tool_name}'")
            
            # Determine if tool expects native Python objects or strings
            preserve_objects = self._should_preserve_objects(tool_name)
            
            # Substitute variables in parameters using unified expression processing
            substituted_params = substitute_in_object(params, context.variables, preserve_objects=preserve_objects)
            
            # Special handling for string params - try to parse as JSON if it looks like JSON
            if isinstance(substituted_params, str):
                # If the entire params is a JSON string, parse it
                substituted_params = self._process_single_string_param(substituted_params, tool_name, context.step_number)
            
            logger.debug(f"Parameters after substitution: {str(substituted_params)[:1000] + '...' if len(str(substituted_params)) > 1000 else str(substituted_params)}")
                        
            # Execute the tool
            if asyncio.iscoroutinefunction(self.tool_runner):
                tool_result = await self.tool_runner(tool_name, substituted_params)
            else:
                tool_result = self.tool_runner(tool_name, substituted_params)
            
            # Parse and store result - extract and parse JSON from TextContent
            if isinstance(tool_result, list) and len(tool_result) > 0:
                first_result = tool_result[0]
                # If it's a TextContent object, extract the text
                if hasattr(first_result, 'text'):
                    text_content = first_result.text
                    # Try to parse as JSON, but if it fails, keep as text
                    try:
                        import json
                        parsed_result = json.loads(text_content)
                        logger.debug(f"Successfully parsed tool result as JSON")
                    except (json.JSONDecodeError, AttributeError):
                        # Not JSON - keep as plain text (useful for CSV, HTML, etc.)
                        parsed_result = text_content
                        logger.debug(f"Tool result kept as plain text (not JSON)")
                else:
                    parsed_result = first_result
            else:
                parsed_result = tool_result
            
            # Ensure result is JSON-compatible before storing
            json_compatible_result = self._ensure_json_compatible(parsed_result)
            
            # Check if tool result indicates failure
            if isinstance(json_compatible_result, dict) and json_compatible_result.get("success") is False:
                error_msg = f"Step {context.step_number} tool '{tool_name}' reported failure: {json_compatible_result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return PipelineResult(
                    success=False,
                    error=error_msg,
                    step=context.step_number,
                    tool=tool_name,
                    context=context.variables
                )
            
            if output_var:
                context.variables[output_var] = json_compatible_result
                logger.debug(f"Stored JSON-compatible result in variable '{output_var}': {type(json_compatible_result).__name__}")
                
                # Save output log if output_log is specified
                if "output_log" in step:
                    try:
                        self._save_output_log(step["output_log"], json_compatible_result)
                    except Exception as log_error:
                        logger.warning(f"Failed to save output log: {log_error}")
            
            return PipelineResult(success=True, context=context.variables)
            
        except Exception as e:
            error_msg = f"Step {context.step_number} tool '{tool_name}' failed: {str(e)}"
            logger.error(error_msg)
            return PipelineResult(
                success=False,
                error=error_msg,
                step=context.step_number,
                tool=tool_name,
                context=context.variables
            )
    
    @property
    def strategy_name(self) -> str:
        return "Tool"
    
    def _ensure_json_compatible(self, obj: Any) -> Any:
        """Ensure object is JSON-serializable."""
        import json
        from datetime import datetime
        from decimal import Decimal
        
        try:
            # Test if object is already JSON-serializable
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            pass
        
        # Convert problematic types
        if isinstance(obj, tuple):
            return [self._ensure_json_compatible(item) for item in obj]
        elif isinstance(obj, set):
            return [self._ensure_json_compatible(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            return {k: self._ensure_json_compatible(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, dict):
            return {k: self._ensure_json_compatible(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._ensure_json_compatible(item) for item in obj]
        else:
            return str(obj)
    
    def _should_preserve_objects(self, tool_name: str) -> bool:
        """Determine if tool expects native Python objects or strings."""
        # Tools that work with JSON data structures need Python objects
        python_object_tools = {
            "lng_json_to_csv",      # Expects json_data as array/object
            "lng_javascript_execute", # parameters field expects objects
        }
        
        return tool_name in python_object_tools
    
    def _save_output_log(self, log_name: str, output_data: Any) -> None:
        """Save output data to a timestamped log file."""
        import os
        import json
        from datetime import datetime
        
        # Create debug logs directory if it doesn't exist
        import mcp_server
        project_root = os.path.dirname(os.path.dirname(mcp_server.__file__))
        debug_dir = os.path.join(project_root, "mcp_server", "logs", "pipeline")
        os.makedirs(debug_dir, exist_ok=True)
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        filename = f"{timestamp}_{log_name}.log"
        file_path = os.path.join(debug_dir, filename)
        
        # Save data as pretty-printed JSON
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved output log: {filename}")
        except Exception as e:
            logger.error(f"Failed to save output log {filename}: {e}")
            raise
    
    def _process_single_string_param(self, params_string: str, tool_name: str, step_number: int) -> Dict[str, Any]:
        """
        Process a single string that should be parsed as JSON parameters.
        
        This handles the case where entire params field is a JSON string from webhook.
        """
        logger.info(f"Step {step_number}: Processing single string param for tool '{tool_name}': {params_string}")
        logger.info(f"Step {step_number}: String type: {type(params_string)}")
        
        if not isinstance(params_string, str):
            logger.info(f"Step {step_number}: Not a string, returning as-is")
            return params_string
            
        stripped_value = params_string.strip()
        logger.info(f"Step {step_number}: Stripped value: '{stripped_value}'")
        
        # First, try to parse as JSON
        if (stripped_value.startswith('{') and stripped_value.endswith('}')) or \
           (stripped_value.startswith('[') and stripped_value.endswith(']')):
            try:
                import json
                parsed_params = json.loads(stripped_value)
                logger.info(f"Step {step_number}: Successfully parsed as JSON: {parsed_params}")
                return parsed_params
            except (json.JSONDecodeError, ValueError) as e:
                logger.info(f"Step {step_number}: JSON parsing failed: {e}, trying Python eval")
        
        # If JSON parsing fails, try Python eval (for string representation of dict)
        if stripped_value.startswith("{'") and stripped_value.endswith("'}"):
            try:
                import ast
                parsed_params = ast.literal_eval(stripped_value)
                logger.info(f"Step {step_number}: Successfully parsed as Python dict: {parsed_params}")
                return parsed_params
            except (ValueError, SyntaxError) as e:
                logger.warning(f"Step {step_number}: Python eval parsing failed: {e}")
                
        # If both fail, return empty dict (so tool gets no params)
        logger.info(f"Step {step_number}: Returning empty dict as fallback")
        return {}
