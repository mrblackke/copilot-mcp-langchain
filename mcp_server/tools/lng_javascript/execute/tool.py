import mcp.types as types
import json
import logging
from py_mini_racer import py_mini_racer
from mcp_server.file_state_manager import FileStateManager

# Get logger
logger = logging.getLogger(__name__)

# Create file state manager for JavaScript functions
javascript_manager = FileStateManager("mcp_server/config/javascript")

async def tool_info() -> dict:
    """Returns information about the lng_javascript_execute tool."""
    return {
        "description": """Execute previously saved JavaScript functions with parameters and full console.log support.

**Function Path Support:**
Functions can be organized in subfolders using "/" notation:
- "functionName" - searches in main javascript folder
- "subfolder/functionName" - searches in specified subfolder

**Console Logging Support:**
JavaScript functions can use console.log, console.warn, and console.error for debugging.
All console messages are automatically captured and logged to both server logs and console output.

**Parameters:**
- `function_name` (string, required): Name of the saved function to execute (supports subfolder paths)
- `parameters` (object, optional): Parameters to pass to the function

**Parameter Handling:**
- Parameters are passed directly as objects/primitives to JavaScript
- No need for JSON string conversion - objects stay objects

**Examples:**
```json
{
    "function_name": "calculateSum",
    "parameters": {"a": 5, "b": 3}
}
```

```json
{
    "function_name": "telemetry/mergeJsons",
    "parameters": {"json_arrays": [{"data": 1}, {"data": 2}]}
}
```

```json
{
    "function_name": "debugExample",
    "parameters": {"data": "test", "debug": true}
}
```

**Console Logging Example:**
```javascript
function debugExample(params) {
    console.log('Function called with:', params);
    console.warn('This is a warning message');
    if (params.debug) {
        console.error('Debug mode enabled');
    }
    return params.data.toUpperCase();
}
```

**Output:**
- Success: Returns actual function result (JSON or text)
- Error: JSON object with error message
- Logs: All console messages appear in server logs with timestamps""",
        "schema": {
            "type": "object",
            "properties": {
                "function_name": {
                    "type": "string", 
                    "description": "Name of the JavaScript function to execute (supports subfolder paths like 'telemetry/functionName')"
                },
                "parameters": {
                    "description": "Parameters to pass to function - can be object, string, number, or any JSON type"
                }
            },
            "required": ["function_name"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Execute JavaScript function."""
    try:
        function_name = parameters.get("function_name", "")
        function_parameters = parameters.get("parameters")
        
        if not function_name:
            return [types.TextContent(type="text", text=json.dumps({"error": "function_name is required"}))]
        
        # Handle function path with subfolders
        if "/" in function_name:
            # Split path and function name
            path_parts = function_name.split("/")
            function_file_name = path_parts[-1]  # Last part is the function name
            
            # Check if this is an absolute path from project root
            if function_name.startswith("mcp_server/projects/"):
                # Use absolute path from project root - extract directory path
                subfolder_path = "/".join(path_parts[:-1])  # Everything before function name
                subfolder_manager = FileStateManager(subfolder_path)
                function_code = subfolder_manager.get(function_file_name, extension=".js")
            else:
                # Use relative path from config/javascript (legacy behavior)
                subfolder_path = "/".join(path_parts[:-1])  # Everything before is the path
                subfolder_manager = FileStateManager(f"mcp_server/config/javascript/{subfolder_path}")
                function_code = subfolder_manager.get(function_file_name, extension=".js")
        else:
            # Load the function from the main javascript folder
            function_code = javascript_manager.get(function_name, extension=".js")
        
        if function_code is None:
            return [types.TextContent(type="text", text=json.dumps({
                "error": f"Function {function_name} not found. Use lng_javascript_add to save it first."
            }))]
        
        # Execute the JavaScript function
        # Extract actual function name from path (last part after /)
        actual_function_name = function_name.split("/")[-1] if "/" in function_name else function_name
        result = execute_javascript_function(function_code, actual_function_name, function_parameters)
        
        # Return the result - if it's already a string (JSON or plain text), return as-is
        if isinstance(result, str):
            return [types.TextContent(type="text", text=result)]
        else:
            # Convert to JSON if it's not a string
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
    except Exception as e:
        function_name = parameters.get("function_name", "unknown")
        error_result = {"error": f"Error executing function '{function_name}': {str(e)}"}
        return [types.TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False))]

def execute_javascript_function(function_code: str, function_name: str, parameters):
    """Execute JavaScript function using PyMiniRacer."""
    try:
        # Create PyMiniRacer context
        ctx = py_mini_racer.MiniRacer()
        
        # Setup console.log capture system
        ctx.eval("""
        var ___logs = [];
        var ___makeLogger = (prefix) => (...args) => {
            var msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
            ___logs.push(prefix + msg);
        };
        console = {
            log: ___makeLogger('[JS LOG] '),
            warn: ___makeLogger('[JS WARN] '),
            error: ___makeLogger('[JS ERROR] ')
        };
        """)
        
        # Evaluate the function code to define the function
        ctx.eval(function_code)
        
        # Call the function with parameters
        if parameters is not None:
            result = ctx.call(function_name, parameters)
        else:
            result = ctx.call(function_name)
        
        # Get and output JS logs
        try:
            logs = ctx.eval('___logs')
            # Convert JSObject to Python list
            log_list = []
            try:
                # Try to get length using JavaScript
                log_count = ctx.eval('___logs.length')
                for i in range(log_count):
                    log_list.append(ctx.eval(f'___logs[{i}]'))
            except:
                # Fallback: iterate directly
                for log in logs:
                    log_list.append(log)
            
            logger.info(f"[DEBUG] Retrieved {len(log_list)} JavaScript logs for '{function_name}' function")
            for i, log in enumerate(log_list):
                logger.info(f"JS Console: {log}") 
        except Exception as e:
            logger.error(f"[DEBUG] Error retrieving JavaScript logs: {e}")
        
        return result
        
    except Exception as e:
        raise Exception(f"JavaScript execution error in function '{function_name}': {str(e)}")
