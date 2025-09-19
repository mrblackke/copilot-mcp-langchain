import mcp.types as types
import json
from mcp_server.file_state_manager import FileStateManager

# Create file state manager for JavaScript functions
javascript_manager = FileStateManager("mcp_server/config/javascript")

async def tool_info() -> dict:
    """Returns information about the lng_javascript_list tool."""
    return {
        "description": """List all saved JavaScript functions.

**Parameters:**
- No parameters required

**Example:**
```json
{}
```

**Output:**
- Success: JSON object with list of saved functions
- Error: JSON object with error message""",
        "schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """List all saved JavaScript functions."""
    try:
        # Get all JavaScript functions
        function_names = javascript_manager.list_files(extension=".js")
        
        if not function_names:
            result = {
                "message": "No JavaScript functions saved",
                "functions": []
            }
        else:
            result = {
                "message": f"Found {len(function_names)} saved JavaScript function(s)",
                "functions": function_names,
                "storage_directory": "mcp_server/config/javascript/"
            }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
    except Exception as e:
        error_result = {"error": f"Error listing functions: {str(e)}"}
        return [types.TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False))]
