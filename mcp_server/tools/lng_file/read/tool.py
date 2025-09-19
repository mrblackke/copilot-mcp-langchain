import mcp.types as types
import os
import json

async def tool_info() -> dict:
    """Returns information about the lng_file_read tool."""
    return {
        "description": """Reads text files with encoding support and optional offset/limit functionality.

**Parameters:**
- `file_path` (string, required): Absolute or relative path to the file to read.
- `encoding` (string, optional): File encoding. Default: 'utf-8'. Supported: 'utf-8', 'ascii', 'cp1251', 'latin-1', etc.
- `offset` (integer, optional): Number of lines to skip from the beginning. Default: 0.
- `limit` (integer, optional): Maximum number of lines to read. If not specified, reads all lines from offset.
- `output_format` (string, optional): Output format. Default: 'plain_text'. Options: 'plain_text', 'json'.

**Example Usage:**
- Read entire file: `{"file_path": "data.txt"}`
- Read with specific encoding: `{"file_path": "data.txt", "encoding": "cp1251"}`
- Read lines 10-20: `{"file_path": "data.txt", "offset": 9, "limit": 10}`
- Read with JSON output: `{"file_path": "data.txt", "output_format": "json"}`

**Returns:**
- Plain text content by default (raw file content)
- JSON with content and metadata when output_format="json"
- JSON with error details on failure (regardless of output_format)

This tool is cross-platform and handles both absolute and relative file paths.""",
        "schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read (absolute or relative)"
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8"
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of lines to skip from the beginning (default: 0)",
                    "default": 0,
                    "minimum": 0
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to read (optional)",
                    "minimum": 1
                },
                "output_format": {
                    "type": "string",
                    "description": "Output format (default: plain_text)",
                    "enum": ["plain_text", "json"],
                    "default": "plain_text"
                }
            },
            "required": ["file_path"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Reads text files with encoding support and optional offset/limit functionality."""
    try:
        # Extract parameters
        file_path = parameters.get("file_path", "")
        encoding = parameters.get("encoding", "utf-8")
        offset = parameters.get("offset", 0)
        limit = parameters.get("limit")
        output_format = parameters.get("output_format", "plain_text")
        
        if not file_path:
            error_metadata = {
                "operation": "file_read",
                "success": False,
                "error": "file_path parameter is required"
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        # Convert relative path to absolute if needed
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        
        # Check if file exists
        if not os.path.exists(file_path):
            error_metadata = {
                "operation": "file_read",
                "file_path": file_path,
                "success": False,
                "error": f"File not found: {file_path}"
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        # Check if it's a file (not directory)
        if not os.path.isfile(file_path):
            error_metadata = {
                "operation": "file_read",
                "file_path": file_path,
                "success": False,
                "error": f"Path is not a file: {file_path}"
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        # Get file metadata
        file_size = os.path.getsize(file_path)
        file_mtime = os.path.getmtime(file_path)
        
        # Read file
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
        except UnicodeDecodeError as e:
            error_metadata = {
                "operation": "file_read",
                "file_path": file_path,
                "encoding": encoding,
                "success": False,
                "error": f"Unable to decode file with encoding '{encoding}': {str(e)}"
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        except PermissionError:
            error_metadata = {
                "operation": "file_read",
                "file_path": file_path,
                "success": False,
                "error": f"Permission denied reading file: {file_path}"
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            error_metadata = {
                "operation": "file_read",
                "file_path": file_path,
                "success": False,
                "error": f"Error reading file: {str(e)}"
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        total_lines = len(lines)
        
        # Apply offset and limit
        if offset >= total_lines:
            selected_lines = []
        else:
            end_index = offset + limit if limit else total_lines
            selected_lines = lines[offset:end_index]
        
        # Prepare content
        content = ''.join(selected_lines)
        
        # Create metadata
        metadata = {
            "operation": "file_read",
            "file_path": file_path,
            "encoding": encoding,
            "file_size_bytes": file_size,
            "total_lines": total_lines,
            "offset": offset,
            "lines_read": len(selected_lines),
            "success": True
        }
        
        if limit:
            metadata["limit"] = limit
        
        # Return result based on output_format
        if output_format == "json":
            result = {
                "content": content,
                "metadata": metadata
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        else:
            # Default: plain text
            return [types.TextContent(type="text", text=content)]
        
    except Exception as e:
        error_metadata = {
            "operation": "file_read",
            "success": False,
            "error": str(e)
        }
        result = json.dumps({"metadata": error_metadata}, indent=2)
        return [types.TextContent(type="text", text=result)]
