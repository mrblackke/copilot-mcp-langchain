import mcp.types as types
import os
import json
from datetime import datetime

async def tool_info() -> dict:
    """Returns information about the lng_file_write tool."""
    return {
        "description": """Writes text content to files with encoding support and multiple write modes.

**Parameters:**
- `file_path` (string, required): Absolute or relative path to the file to write.
- `content` (string, required): Text content to write to the file.
- `encoding` (string, optional): File encoding. Default: 'utf-8'. Supported: 'utf-8', 'ascii', 'cp1251', 'latin-1', etc.
- `mode` (string, optional): Write mode. Default: 'create'. Options:
  - 'create': Create new file (fails if file exists)
  - 'overwrite': Create new file or overwrite existing
  - 'append': Append to existing file (creates if doesn't exist)

**Example Usage:**
- Create new file: `{"file_path": "output.txt", "content": "Hello World"}`
- Overwrite file: `{"file_path": "output.txt", "content": "New content", "mode": "overwrite"}`
- Append to file: `{"file_path": "log.txt", "content": "New log entry\\n", "mode": "append"}`

**Returns:**
- JSON with operation metadata and status information
- Error information in metadata if operation fails

This tool is cross-platform and automatically creates directories if they don't exist.""",
        "schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write (absolute or relative)"
                },
                "content": {
                    "type": "string",
                    "description": "Text content to write to the file"
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8"
                },
                "mode": {
                    "type": "string",
                    "description": "Write mode (default: create)",
                    "enum": ["create", "overwrite", "append"],
                    "default": "create"
                }
            },
            "required": ["file_path", "content"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Writes text content to files with encoding support and multiple write modes."""
    try:
        # Extract parameters
        file_path = parameters.get("file_path", "")
        content = parameters.get("content")  # Remove default empty string
        encoding = parameters.get("encoding", "utf-8")
        mode = parameters.get("mode", "create")
        
        if not file_path:
            error_metadata = {
                "operation": "file_write",
                "success": False,
                "error": "file_path parameter is required",
                "timestamp": datetime.now().isoformat()
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        if content is None:  # Allow empty string but not None
            error_metadata = {
                "operation": "file_write",
                "success": False,
                "error": "content parameter is required",
                "timestamp": datetime.now().isoformat()
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        # Convert relative path to absolute if needed
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        
        # Check mode and file existence
        file_exists = os.path.exists(file_path)
        
        if mode == "create" and file_exists:
            error_metadata = {
                "operation": "file_write",
                "file_path": file_path,
                "mode": mode,
                "success": False,
                "error": f"File already exists. Use mode 'overwrite' to replace or 'append' to add content: {file_path}",
                "timestamp": datetime.now().isoformat()
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        # Get directory path and create if needed
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                created_dirs = True
            except Exception as e:
                error_metadata = {
                    "operation": "file_write",
                    "file_path": file_path,
                    "success": False,
                    "error": f"Unable to create directory {dir_path}: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                result = json.dumps({"metadata": error_metadata}, indent=2)
                return [types.TextContent(type="text", text=result)]
        else:
            created_dirs = False
        
        # Store original file info if exists
        original_size = 0
        if file_exists:
            try:
                original_size = os.path.getsize(file_path)
            except:
                pass
        
        # Determine file opening mode
        if mode == "append":
            file_mode = "a"
        else:  # create or overwrite
            file_mode = "w"
        
        # Write file
        try:
            with open(file_path, file_mode, encoding=encoding) as f:
                f.write(content)
        except PermissionError:
            error_metadata = {
                "operation": "file_write",
                "file_path": file_path,
                "success": False,
                "error": f"Permission denied writing to file: {file_path}",
                "timestamp": datetime.now().isoformat()
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        except UnicodeEncodeError as e:
            error_metadata = {
                "operation": "file_write",
                "file_path": file_path,
                "encoding": encoding,
                "success": False,
                "error": f"Unable to encode content with encoding '{encoding}': {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        except OSError as e:
            error_metadata = {
                "operation": "file_write",
                "file_path": file_path,
                "success": False,
                "error": f"Disk operation failed (possibly insufficient space): {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            error_metadata = {
                "operation": "file_write",
                "file_path": file_path,
                "success": False,
                "error": f"Error writing file: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        # Get final file info
        try:
            final_size = os.path.getsize(file_path)
            file_mtime = os.path.getmtime(file_path)
        except Exception as e:
            error_metadata = {
                "operation": "file_write",
                "file_path": file_path,
                "success": False,
                "error": f"File was written but unable to get file info: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        # Create metadata
        content_lines = content.count('\n') + (1 if content else 0)
        content_chars = len(content)
        
        metadata = {
            "operation": "file_write",
            "file_path": file_path,
            "encoding": encoding,
            "mode": mode,
            "content_characters": content_chars,
            "content_lines": content_lines,
            "file_size_bytes": final_size,
            "file_existed": file_exists,
            "directories_created": created_dirs,
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "message": "File operation completed successfully"
        }
        
        if file_exists and mode != "create":
            metadata["original_size_bytes"] = original_size
            if mode == "append":
                metadata["bytes_added"] = final_size - original_size
            elif mode == "overwrite":
                metadata["size_change_bytes"] = final_size - original_size
        
        # Create result
        result = json.dumps({"metadata": metadata}, indent=2)
        return [types.TextContent(type="text", text=result)]
        
    except Exception as e:
        error_metadata = {
            "operation": "file_write",
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        result = json.dumps({"metadata": error_metadata}, indent=2)
        return [types.TextContent(type="text", text=result)]
