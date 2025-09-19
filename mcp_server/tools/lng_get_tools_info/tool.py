import mcp.types as types
import mcp_server.tools.tool_registry as tools

async def tool_info() -> dict:
    """Returns information about the lng_get_tools_info tool."""
    return {
        "description": """Returns detailed information about specific tools.

**Parameters:**
- `tools` (string, optional): Comma-separated list of tool names to get info for. If not provided, returns info about all tools.
- `format` (string, optional): Output format - 'markdown' (default) or 'json'. JSON format returns structured data for API consumption.

**Example Usage:**
- Get info for specific tools: `{"tools": "lng_file_list,lng_file_read"}`
- Get info for single tool: `{"tools": "lng_file_list"}`
- Get info for all tools: `{}` (no parameters)
- Get JSON format: `{"format": "json"}` or `{"tools": "lng_file_read", "format": "json"}`

This tool helps you understand the capabilities, parameters, and usage examples of specific tools in the system.""",
        "schema": {
            "type": "object",
            "properties": {
                "tools": {
                    "type": "string",
                    "description": "Comma-separated list of tool names to get information for"
                },
                "format": {
                    "type": "string",
                    "enum": ["markdown", "json"],
                    "description": "Output format - 'markdown' (default) or 'json'"
                }
            }
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Returns information about the available langchain tools."""
    
    tools_arg = parameters.get("tools", None)
    format_arg = parameters.get("format", "markdown")  # Default to markdown
    
    try:
        # Get all tools information
        tool_info_list = await tools.tools_info()
        
        # If specific tools requested, filter the results
        filtered_tools = []
        missing_tools = []
        
        if tools_arg:
            requested_tools = [tool.strip() for tool in tools_arg.split(',')]
            
            for tool_name in requested_tools:
                found = False
                for tool in tool_info_list:
                    if tool['name'] == tool_name:
                        filtered_tools.append(tool)
                        found = True
                        break
                if not found:
                    missing_tools.append(tool_name)
        else:
            # Use all tools if none specified
            filtered_tools = tool_info_list
        
        # Return JSON format if requested
        if format_arg == "json":
            import json
            json_response = {
                "api_version": "1.0.0",
                "success": True,
                "total_tools": len(filtered_tools),
                "requested_tools": len(filtered_tools) if tools_arg else len(tool_info_list),
                "missing_tools": missing_tools if tools_arg else [],
                "tools": []
            }
            
            # Convert tools to API-friendly format
            for tool in filtered_tools:
                # Extract basic info from the tool description
                tool_data = {
                    "name": tool['name'],
                    "description": tool['description'],
                    "short_description": tool['description'].split('\n')[0] if tool['description'] else "",
                    "category": extract_category_from_name(tool['name']),
                    "parameters": extract_parameters_from_schema(tool.get('schema', {}))
                }
                json_response["tools"].append(tool_data)
            
            return [types.TextContent(type="text", text=json.dumps(json_response, indent=2))]
        
        # Original markdown format
        if tools_arg:
            # Build markdown for filtered tools
            markdown_content = f"# Langchain MCP Tools (Filtered: {len(filtered_tools)} of {len(tool_info_list)} requested)\n\n"
            
            if missing_tools:
                markdown_content += f"**⚠️ Missing tools:** {', '.join(missing_tools)}\n\n"
            
            markdown_content += "This document describes the requested tools available in the Langchain Model Context Protocol (MCP) implementation.\n\n"
            markdown_content += "## Requested Tools\n\n"
            
            # Add each filtered tool's information
            for i, tool in enumerate(filtered_tools, 1):
                markdown_content += f"### {i}. `{tool['name']}`\n\n"
                markdown_content += f"{tool['description']}\n\n"
                
        else:
            # Show all tools
            markdown_content = "# Langchain MCP Tools\n\n"
            markdown_content += "This document describes the tools available in the Langchain Model Context Protocol (MCP) implementation.\n\n"
            markdown_content += f"## Available Tools (Total: {len(tool_info_list)})\n\n"
            
            # Add each tool's information
            for i, tool in enumerate(tool_info_list, 1):
                markdown_content += f"### {i}. `{tool['name']}`\n\n"
                markdown_content += f"{tool['description']}\n\n"
        
        return [types.TextContent(type="text", text=markdown_content)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error retrieving tools information: {str(e)}")]


def extract_category_from_name(tool_name: str) -> str:
    """Extract category from tool name by looking at tool registry module path."""
    # Get the tool from registry to access module_path
    for tool in tools.tool_definitions:
        if tool["name"] == tool_name:
            module_path = tool["module_path"]
            return extract_category_from_module_path(module_path)
    
    # Fallback if not found in registry
    return "Unknown"


def extract_category_from_module_path(module_path: str) -> str:
    """Extract category from tool module path dynamically."""
    # Example: mcp_server.tools.lng_file.read.tool -> lng_file/read
    # Example: mcp_server.tools.lng_llm.rag.tool -> lng_llm/rag  
    # Example: mcp_server.tools.lng_math_calculator.tool -> lng_math_calculator
    
    path_parts = module_path.split('.')
    
    # Remove mcp_server.tools prefix and .tool suffix
    if len(path_parts) >= 3 and path_parts[0] == 'mcp_server' and path_parts[1] == 'tools':
        tool_parts = path_parts[2:]  # Remove 'mcp_server.tools'
        if tool_parts and tool_parts[-1] == 'tool':
            tool_parts = tool_parts[:-1]  # Remove 'tool'
        
        if not tool_parts:
            return "Unknown"
            
        # Format category based on depth
        if len(tool_parts) == 1:
            # Single level: lng_file -> File
            return format_category_name(tool_parts[0])
        else:
            # Multi-level: lng_llm.rag -> AI/LLM / RAG
            main_category = format_category_name(tool_parts[0])
            sub_category = format_category_name(tool_parts[1])
            return f"{main_category} / {sub_category}"
    
    return "Unknown"


def format_category_name(raw_name: str) -> str:
    """Format category name from directory name dynamically without hardcode."""
    # Remove lng_ prefix if present
    if raw_name.startswith('lng_'):
        clean_name = raw_name[4:]  # Remove 'lng_' prefix
    else:
        clean_name = raw_name
    
    # Replace underscores with spaces and title case
    return clean_name.replace('_', ' ').title()


def extract_parameters_from_schema(schema: dict) -> list:
    """Extract parameters from tool schema."""
    parameters = []
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    
    for param_name, param_info in properties.items():
        param_data = {
            "name": param_name,
            "type": param_info.get('type', 'string'),
            "required": param_name in required,
            "description": param_info.get('description', '')
        }
        
        # Add enum values if present
        if 'enum' in param_info:
            param_data['enum'] = param_info['enum']
            
        parameters.append(param_data)
    
    return parameters


def parse_tool_parameters(tool):
    """Parse tool parameters from inputSchema or schema"""
    # Try inputSchema first (more detailed)
    if 'inputSchema' in tool:
        schema = tool['inputSchema']
    elif 'schema' in tool:
        schema = tool['schema']
    else:
        return []
    
    if 'properties' in schema:
        params = []
        required = schema.get('required', [])
        
        for param_name, param_info in schema['properties'].items():
            param = {
                "name": param_name,
                "type": param_info.get('type', 'string'),
                "required": param_name in required,
                "description": param_info.get('description', 'No description')
            }
            
            # Add enum values if available
            if 'enum' in param_info:
                param['enum'] = param_info['enum']
                
            # Add default value if available
            if 'default' in param_info:
                param['default'] = param_info['default']
                
            params.append(param)
        
        return params
    
    return []


def extract_full_schema(tool):
    """Extract complete JSON schema for tool"""
    if 'inputSchema' in tool:
        return tool['inputSchema']
    elif 'schema' in tool:
        return tool['schema']
    return {}