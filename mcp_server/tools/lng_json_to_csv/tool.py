import mcp.types as types
import json
from typing import List, Dict, Any, Optional, Union
import re
import os
import pathlib

# Import our Java-compatible classes
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'stuff'))
from json_to_csv import JsonToCsv

async def tool_info() -> dict:
    """Returns information about the lng_json_to_csv tool."""
    return {
        "description": """Converts JSON data to CSV or Markdown format using Matrix-based algorithm (Java-compatible).

**Two modes of operation:**

1. **Text Mode** (default):
   - `json_data` (object/array, required): JSON data as object or array
   - Returns converted result as text

2. **File Mode**:
   - `input_file_path` (string, required): Path to JSON file
   - `output_file_path` (string, required): Path for output CSV/Markdown file
   - Returns status message with paths

**Parameters:**
- `json_data` (object/array, optional): The JSON data to convert (Text Mode) - must be object or array.
- `input_file_path` (string, optional): Path to input JSON file (File Mode).
- `output_file_path` (string, optional): Path to output file (File Mode).
- `format` (string, optional): Output format - 'csv' or 'markdown'. Default: 'csv'.
- `column_delimiter` (string, optional): Column separator. Default: ','.
- `cell_left_delimiter` (string, optional): Left cell delimiter for escaping. Default: '"'.
- `cell_right_delimiter` (string, optional): Right cell delimiter for escaping. Default: '"'.
- `line_chars_need_to_be_escaped_with_cell_delimiter` (string, optional): Characters that need escaping. Default: '\\n",'.
- `header_delimiter` (string, optional): Header delimiter for markdown format. Default: null.
- `line_replacements` (array, optional): String replacements like ["\\"==>\\"\\""]. Default: ["\\"==>\\"\\""]. 
- `padding_to_max_cell_length` (boolean, optional): Pad cells to max length. Default: false.
- `remove_headers_duplicates` (boolean, optional): Remove duplicate headers. Default: true.

**Mode Selection:**
- Use Text Mode: provide `json_data` parameter
- Use File Mode: provide both `input_file_path` and `output_file_path` parameters

**Example Usage:**
- Convert simple JSON array to CSV
- Support complex nested structures
- Handle arrays within objects
- Escape special characters properly
- Process large files efficiently with File Mode

This tool flattens nested JSON structures into tabular format, preserving hierarchy through column headers.""",
        "schema": {
            "type": "object",
            "properties": {
                "json_data": {
                    "type": "array", 
                    "items": {
                        "type": "object"
                    },
                    "description": "JSON data to convert to CSV/Markdown (Text Mode) - array of objects"
                },
                "input_file_path": {
                    "type": "string",
                    "description": "Path to input JSON file (File Mode)"
                },
                "output_file_path": {
                    "type": "string",
                    "description": "Path to output CSV/Markdown file (File Mode)"
                },
                "format": {
                    "type": "string",
                    "enum": ["csv", "markdown"],
                    "default": "csv",
                    "description": "Output format"
                },
                "column_delimiter": {
                    "type": "string",
                    "default": ",",
                    "description": "Column delimiter"
                },
                "cell_left_delimiter": {
                    "type": "string",
                    "default": "\"",
                    "description": "Left cell delimiter for escaping"
                },
                "cell_right_delimiter": {
                    "type": "string", 
                    "default": "\"",
                    "description": "Right cell delimiter for escaping"
                },
                "line_chars_need_to_be_escaped_with_cell_delimiter": {
                    "type": "string",
                    "default": "\n\",",
                    "description": "Characters that need escaping"
                },
                "header_delimiter": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "Header delimiter (for markdown)"
                },
                "line_replacements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["\"==>\"\""],
                    "description": "String replacements"
                },
                "padding_to_max_cell_length": {
                    "type": "boolean",
                    "default": False,
                    "description": "Pad cells to max length"
                },
                "remove_headers_duplicates": {
                    "type": "boolean",
                    "default": True,
                    "description": "Remove duplicate headers"
                }
            },
            "required": []
        }
    }

def json_to_csv(json_data: str, 
                column_delimiter: str = ",",
                cell_left_delimiter: Optional[str] = "\"",
                cell_right_delimiter: Optional[str] = "\"", 
                line_chars_need_to_be_escaped_with_cell_delimiter: Optional[str] = "\n\",",
                header_delimiter: Optional[str] = None,
                line_replacements: Optional[List[str]] = None,
                padding_to_max_cell_length: bool = False,
                remove_headers_duplicates: bool = True) -> str:
    """Convert JSON to CSV format."""
    
    # Set default line replacements if None
    if line_replacements is None:
        line_replacements = ["\"==>\"\""]
    
    # Use the Java-compatible implementation
    return JsonToCsv._json_to_csv(
        json_data,
        column_delimiter,
        cell_left_delimiter,
        cell_right_delimiter,
        line_chars_need_to_be_escaped_with_cell_delimiter,
        header_delimiter,
        line_replacements,
        padding_to_max_cell_length,
        remove_headers_duplicates
    )       

def json_to_markdown(json_data: str) -> str:
    """Convert JSON to Markdown table format."""
    return JsonToCsv.json_to_markdown(json_data)

def read_json_file(file_path: str) -> str:
    """Read JSON data from file."""
    try:
        # Convert to absolute path and resolve any relative paths
        absolute_path = os.path.abspath(file_path)
        
        # Check if file exists
        if not os.path.exists(absolute_path):
            raise FileNotFoundError(f"Input file not found: {absolute_path}")
            
        # Check if it's a file (not directory)
        if not os.path.isfile(absolute_path):
            raise ValueError(f"Path is not a file: {absolute_path}")
            
        # Read file content
        with open(absolute_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Validate JSON
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {absolute_path}: {str(e)}")
            
        return content
        
    except Exception as e:
        raise Exception(f"Error reading JSON file '{file_path}': {str(e)}")

def write_output_file(file_path: str, content: str) -> str:
    """Write content to output file."""
    try:
        # Convert to absolute path
        absolute_path = os.path.abspath(file_path)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(absolute_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        # Write content to file
        with open(absolute_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Return absolute path for confirmation
        return absolute_path
        
    except Exception as e:
        raise Exception(f"Error writing output file '{file_path}': {str(e)}")

def get_file_size_info(file_path: str) -> dict:
    """Get file size information."""
    try:
        absolute_path = os.path.abspath(file_path)
        if os.path.exists(absolute_path):
            size_bytes = os.path.getsize(absolute_path)
            # Convert to human readable format
            if size_bytes < 1024:
                size_str = f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                
            return {
                "size_bytes": size_bytes,
                "size_formatted": size_str,
                "exists": True
            }
        else:
            return {"exists": False}
    except Exception:
        return {"exists": False}

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Convert JSON data to CSV or Markdown format in Text Mode or File Mode."""
    try:
        # Check which mode to use
        input_file_path = parameters.get("input_file_path")
        output_file_path = parameters.get("output_file_path") 
        json_data = parameters.get("json_data")
        
        # Determine mode
        file_mode = bool(input_file_path and output_file_path)
        text_mode = bool(json_data)
        
        if file_mode and text_mode:
            return [types.TextContent(type="text", text=json.dumps({
                "error": "Cannot use both Text Mode (json_data) and File Mode (input_file_path, output_file_path) parameters simultaneously. Choose one mode."
            }))]
            
        if not file_mode and not text_mode:
            return [types.TextContent(type="text", text=json.dumps({
                "error": "No input provided. Use Text Mode (json_data parameter) or File Mode (input_file_path and output_file_path parameters)."
            }))]
            
        # Get conversion parameters (same for both modes)
        format_type = parameters.get("format", "csv")
        column_delimiter = parameters.get("column_delimiter", ",")
        cell_left_delimiter = parameters.get("cell_left_delimiter", "\"")
        cell_right_delimiter = parameters.get("cell_right_delimiter", "\"")
        line_chars_need_to_be_escaped_with_cell_delimiter = parameters.get(
            "line_chars_need_to_be_escaped_with_cell_delimiter", "\n\","
        )
        header_delimiter = parameters.get("header_delimiter", None)
        line_replacements = parameters.get("line_replacements", ["\"==>\"\""])
        padding_to_max_cell_length = parameters.get("padding_to_max_cell_length", False)
        remove_headers_duplicates = parameters.get("remove_headers_duplicates", True)
        
        # FILE MODE
        if file_mode:
            try:
                # Read input file
                input_info = get_file_size_info(input_file_path)
                json_data = read_json_file(input_file_path)
                
                # Convert based on format
                if format_type == "markdown":
                    result = json_to_markdown(json_data)
                else:
                    result = json_to_csv(
                        json_data,
                        column_delimiter=column_delimiter,
                        cell_left_delimiter=cell_left_delimiter,
                        cell_right_delimiter=cell_right_delimiter,
                        line_chars_need_to_be_escaped_with_cell_delimiter=line_chars_need_to_be_escaped_with_cell_delimiter,
                        header_delimiter=header_delimiter,
                        line_replacements=line_replacements,
                        padding_to_max_cell_length=padding_to_max_cell_length,
                        remove_headers_duplicates=remove_headers_duplicates
                    )
                
                # Write output file
                actual_output_path = write_output_file(output_file_path, result)
                output_info = get_file_size_info(actual_output_path)
                
                # Return success message with file information
                response = {
                    "mode": "file",
                    "success": True,
                    "message": f"Successfully converted JSON to {format_type.upper()}",
                    "input_file": {
                        "path": os.path.abspath(input_file_path),
                        "size": input_info.get("size_formatted", "unknown")
                    },
                    "output_file": {
                        "path": actual_output_path,
                        "size": output_info.get("size_formatted", "unknown"),
                        "format": format_type
                    }
                }
                
                return [types.TextContent(type="text", text=json.dumps(response, indent=2))]
                
            except Exception as e:
                return [types.TextContent(type="text", text=json.dumps({
                    "mode": "file",
                    "success": False,
                    "error": str(e),
                    "input_file_path": input_file_path,
                    "output_file_path": output_file_path
                }))]
        
        # TEXT MODE
        else:
            # json_data should be already parsed JSON object/array
            if json_data is None:
                return [types.TextContent(type="text", text=json.dumps({"error": "json_data is required for text mode"}))]
            
            # Validate that json_data is object or array (not string, number, etc.)
            if not isinstance(json_data, (dict, list)):
                return [types.TextContent(type="text", text=json.dumps({
                    "error": f"json_data must be an object or array, not {type(json_data).__name__}. Use File Mode for processing JSON strings."
                }))]
            
            # Convert JSON object/array to string for internal processing
            json_data_str = json.dumps(json_data)
                
            # Convert based on format
            if format_type == "markdown":
                result = json_to_markdown(json_data_str)
            else:
                result = json_to_csv(
                    json_data_str,
                    column_delimiter=column_delimiter,
                    cell_left_delimiter=cell_left_delimiter,
                    cell_right_delimiter=cell_right_delimiter,
                    line_chars_need_to_be_escaped_with_cell_delimiter=line_chars_need_to_be_escaped_with_cell_delimiter,
                    header_delimiter=header_delimiter,
                    line_replacements=line_replacements,
                    padding_to_max_cell_length=padding_to_max_cell_length,
                    remove_headers_duplicates=remove_headers_duplicates
                )
                
            return [types.TextContent(type="text", text=result)]
        
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]