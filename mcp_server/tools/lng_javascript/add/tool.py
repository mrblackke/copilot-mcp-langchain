import mcp.types as types
import json
from mcp_server.file_state_manager import FileStateManager

# Create file state manager for JavaScript functions
javascript_manager = FileStateManager("mcp_server/config/javascript")

async def tool_info() -> dict:
    """Returns information about the lng_javascript_add tool."""
    return {
        "description": """Save JavaScript functions to filesystem for later execution.

**Function Path Support:**
Functions can be organized in subfolders using "/" notation:
- "functionName" - saves in main javascript folder
- "subfolder/functionName" - saves in specified subfolder under config/javascript/
- "mcp_server/projects/projectName/javascript/functionName" - saves in project-specific location

**Parameters:**
- `function_name` (string, required): Name of the function (must match function declaration)
- `function_code` (string, required): JavaScript function code (must be declared function, not arrow function)

**Function Requirements:**
- Must be declared functions (not arrow functions)
- Function name in code must match the actual function name (last part after /)
- Functions can contain any JavaScript code including async/await
- Functions are stored with .js extension

**Examples:**
```json
{
    "function_name": "calculateSum", 
    "function_code": "function calculateSum(params) { return params.a + params.b; }"
}
```

```json
{
    "function_name": "telemetry/processData", 
    "function_code": "function processData(params) { return params.data.map(x => x * 2); }"
}
```

```json
{
    "function_name": "mcp_server/projects/myproject/javascript/customFunction", 
    "function_code": "function customFunction(params) { return 'Project result: ' + params.input; }"
}
```

**Output:**
- Success: JSON object with save confirmation
- Error: JSON object with error message""",
        "schema": {
            "type": "object",
            "properties": {
                "function_name": {
                    "type": "string", 
                    "description": "Name of the JavaScript function"
                },
                "function_code": {
                    "type": "string",
                    "description": "JavaScript function code"
                }
            },
            "required": ["function_name", "function_code"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Save JavaScript function to filesystem."""
    try:
        function_name = parameters.get("function_name", "")
        function_code = parameters.get("function_code", "")
        
        if not function_name:
            return [types.TextContent(type="text", text=json.dumps({"error": "function_name is required"}))]
        
        if not function_code:
            return [types.TextContent(type="text", text=json.dumps({"error": "function_code is required"}))]
        
        # Extract actual function name for validation (last part after /)
        actual_function_name = function_name.split("/")[-1] if "/" in function_name else function_name
        
        # Validate that function_code contains a function declaration with the correct name
        if f"function {actual_function_name}" not in function_code:
            return [types.TextContent(type="text", text=json.dumps({
                "error": f"Function code must contain a declared function named {actual_function_name}. Arrow functions are not allowed."
            }))]
        
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
                subfolder_manager.set(function_file_name, function_code, extension=".js")
                storage_path = f"{subfolder_path}/{function_file_name}.js"
            else:
                # Use relative path from config/javascript (legacy behavior)
                subfolder_path = "/".join(path_parts[:-1])  # Everything before is the path
                subfolder_manager = FileStateManager(f"mcp_server/config/javascript/{subfolder_path}")
                subfolder_manager.set(function_file_name, function_code, extension=".js")
                storage_path = f"mcp_server/config/javascript/{function_name}.js"
        else:
            # Save the function to the main javascript folder
            javascript_manager.set(function_name, function_code, extension=".js")
            storage_path = f"mcp_server/config/javascript/{function_name}.js"
        
        result = {
            "message": f"Function '{function_name}' saved successfully",
            "function_name": function_name,
            "storage_path": storage_path
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
    except Exception as e:
        error_result = {"error": f"Error saving function: {str(e)}"}
        return [types.TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False))]
