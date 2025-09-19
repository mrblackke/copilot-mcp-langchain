import mcp.types as types
import os
import json
from pathlib import Path

async def tool_info() -> dict:
    """Returns information about the lng_file_list tool."""
    return {
        "description": """Lists all files and directories using multiple glob patterns.

**Parameters:**
- `patterns` (array, required): List of glob patterns to search for files and directories.
- `base_path` (string, optional): Base directory path for pattern matching. Default: current directory (".").
- `group_by_pattern` (boolean, optional): Group results by pattern. Default: false (flat list with deduplication).
- `path_type` (string, optional): Type of paths to return. Default: 'relative'. Options:
  - 'relative': Return paths relative to base_path
  - 'absolute': Return full absolute paths
- `include_directories` (boolean, optional): Include directories in the listing. Default: true.
- `include_files` (boolean, optional): Include files in the listing. Default: true.
- `show_hidden` (boolean, optional): Include hidden files/directories (starting with '.'). Default: false.
- `output_format` (string, optional): Output format. Default: 'list'. Options:
  - 'list': Simple list of paths
  - 'detailed': Detailed information including size, modified time, type
  - 'json': JSON format with metadata

**Example Usage:**
- List files by patterns: `{"patterns": ["src/**/*.py", "tests/**/*.py", "docs/*.md"]}`
- With grouping: `{"patterns": ["src/**/*.py", "docs/*.md"], "group_by_pattern": true}`
- Custom base path: `{"patterns": ["**/*.txt"], "base_path": "/project/root"}`
- Detailed format: `{"patterns": ["*.py"], "output_format": "detailed"}`

**Returns:**
- Flat list of paths when group_by_pattern=false (default)
- Grouped results by pattern when group_by_pattern=true
- Detailed metadata when output_format="detailed" or "json"
- Error information if operation fails

This tool is cross-platform and handles both absolute and relative paths with glob pattern matching.""",
        "schema": {
            "type": "object",
            "properties": {
                "patterns": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of glob patterns to search for files and directories"
                },
                "base_path": {
                    "type": "string",
                    "description": "Base directory path for pattern matching (default: current directory)",
                    "default": "."
                },
                "group_by_pattern": {
                    "type": "boolean",
                    "description": "Group results by pattern (default: false - flat list with deduplication)",
                    "default": False
                },
                "path_type": {
                    "type": "string",
                    "description": "Type of paths to return (default: relative)",
                    "enum": ["relative", "absolute"],
                    "default": "relative"
                },
                "include_directories": {
                    "type": "boolean",
                    "description": "Include directories in the listing (default: true)",
                    "default": True
                },
                "include_files": {
                    "type": "boolean",
                    "description": "Include files in the listing (default: true)",
                    "default": True
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files/directories (default: false)",
                    "default": False
                },
                "output_format": {
                    "type": "string",
                    "description": "Output format (default: list)",
                    "enum": ["list", "detailed", "json"],
                    "default": "list"
                }
            },
            "required": ["patterns"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Lists all files and directories using multiple glob patterns."""
    try:
        # Extract parameters
        patterns = parameters.get("patterns", [])
        base_path = parameters.get("base_path", ".")
        group_by_pattern = parameters.get("group_by_pattern", False)
        path_type = parameters.get("path_type", "relative")
        include_directories = parameters.get("include_directories", True)
        include_files = parameters.get("include_files", True)
        show_hidden = parameters.get("show_hidden", False)
        output_format = parameters.get("output_format", "list")
        
        # Validate required parameters
        if not patterns:
            error_metadata = {
                "operation": "file_list_patterns",
                "success": False,
                "error": "patterns parameter is required and must be a non-empty list"
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        if not isinstance(patterns, list):
            error_metadata = {
                "operation": "file_list_patterns",
                "success": False,
                "error": "patterns parameter must be a list of strings"
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        # Convert relative base_path to absolute if needed
        if not os.path.isabs(base_path):
            base_path = os.path.abspath(base_path)
        
        # Check if base_path exists
        if not os.path.exists(base_path):
            error_metadata = {
                "operation": "file_list_patterns",
                "base_path": base_path,
                "success": False,
                "error": f"Base path not found: {base_path}"
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        # Check if base_path is a directory
        if not os.path.isdir(base_path):
            error_metadata = {
                "operation": "file_list_patterns",
                "base_path": base_path,
                "success": False,
                "error": f"Base path is not a directory: {base_path}"
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        # Process patterns and collect results
        pattern_results = {}
        all_items = {}  # For deduplication in flat mode
        base_path_obj = Path(base_path)
        
        try:
            for pattern in patterns:
                pattern_items = []
                
                # Apply glob pattern from base_path
                try:
                    paths = base_path_obj.glob(pattern)
                    
                    for path in sorted(paths):
                        # Skip hidden files/directories if not requested
                        if not show_hidden and any(part.startswith('.') for part in path.parts[len(base_path_obj.parts):]):
                            continue
                        
                        # Filter by type
                        if path.is_file() and not include_files:
                            continue
                        if path.is_dir() and not include_directories:
                            continue
                        
                        # Determine path to return
                        if path_type == "absolute":
                            item_path = str(path.absolute())
                        else:  # relative
                            try:
                                item_path = str(path.relative_to(base_path_obj))
                            except ValueError:
                                # Fallback to absolute if relative calculation fails
                                item_path = str(path.absolute())
                        
                        # Collect item information
                        item_info = {
                            "path": item_path,
                            "name": path.name,
                            "type": "directory" if path.is_dir() else "file",
                            "pattern": pattern  # Track which pattern matched
                        }
                        
                        # Add detailed information if requested
                        if output_format in ["detailed", "json"]:
                            try:
                                stat_info = path.stat()
                                item_info.update({
                                    "size": stat_info.st_size if path.is_file() else None,
                                    "modified_time": stat_info.st_mtime,
                                    "permissions": oct(stat_info.st_mode)[-3:],
                                    "is_hidden": path.name.startswith('.'),
                                    "absolute_path": str(path.absolute())
                                })
                            except (OSError, PermissionError):
                                item_info.update({
                                    "size": None,
                                    "modified_time": None,
                                    "permissions": None,
                                    "is_hidden": path.name.startswith('.'),
                                    "absolute_path": str(path.absolute()),
                                    "error": "Unable to get file stats"
                                })
                        
                        pattern_items.append(item_info)
                        
                        # Add to all_items for deduplication (use absolute path as key)
                        abs_path = str(path.absolute())
                        if abs_path not in all_items:
                            all_items[abs_path] = item_info
                
                except Exception as e:
                    # If pattern fails, still include it with empty results
                    pattern_items = []
                
                # Store results for this pattern
                pattern_results[pattern] = pattern_items
        
        except PermissionError:
            error_metadata = {
                "operation": "file_list_patterns",
                "base_path": base_path,
                "success": False,
                "error": f"Permission denied accessing base path: {base_path}"
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            error_metadata = {
                "operation": "file_list_patterns",
                "base_path": base_path,
                "success": False,
                "error": f"Error processing patterns: {str(e)}"
            }
            result = json.dumps({"metadata": error_metadata}, indent=2)
            return [types.TextContent(type="text", text=result)]
        
        # Create metadata
        metadata = {
            "operation": "file_list_patterns",
            "base_path": base_path,
            "patterns": patterns,
            "group_by_pattern": group_by_pattern,
            "path_type": path_type,
            "include_directories": include_directories,
            "include_files": include_files,
            "show_hidden": show_hidden,
            "output_format": output_format,
            "success": True
        }
        
        # Prepare results based on grouping preference
        if group_by_pattern:
            # Group results by pattern
            grouped_results = {}
            total_items = 0
            
            for pattern, items in pattern_results.items():
                grouped_results[pattern] = [item["path"] for item in items]
                total_items += len(items)
            
            metadata["total_items"] = total_items
            metadata["patterns_processed"] = len(patterns)
            
            if output_format == "json":
                result = {
                    "grouped_results": grouped_results,
                    "metadata": metadata
                }
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            elif output_format == "detailed":
                lines = [f"Pattern-based file listing: {base_path}"]
                lines.append(f"Total patterns: {len(patterns)}")
                lines.append(f"Total items: {total_items}")
                lines.append("")
                
                for pattern, paths in grouped_results.items():
                    lines.append(f"Pattern: {pattern} ({len(paths)} items)")
                    for path in paths:
                        lines.append(f"  {path}")
                    lines.append("")
                
                return [types.TextContent(type="text", text="\n".join(lines))]
            else:
                # Default: formatted grouped output
                lines = []
                for pattern, paths in grouped_results.items():
                    lines.append(f"# Pattern: {pattern}")
                    lines.extend(paths)
                    lines.append("")
                
                return [types.TextContent(type="text", text="\n".join(lines))]
        else:
            # Flat list with deduplication
            unique_items = list(all_items.values())
            unique_items.sort(key=lambda x: x["path"])
            
            metadata["total_items"] = len(unique_items)
            metadata["patterns_processed"] = len(patterns)
            
            if output_format == "json":
                result = {
                    "items": unique_items,
                    "metadata": metadata
                }
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            elif output_format == "detailed":
                lines = [f"Multi-pattern file listing: {base_path}"]
                lines.append(f"Patterns: {', '.join(patterns)}")
                lines.append(f"Total items: {len(unique_items)}")
                lines.append("")
                
                for item in unique_items:
                    line = f"{item['type']:>9}: {item['path']}"
                    if item.get('size') is not None:
                        line += f" ({item['size']} bytes)"
                    if item.get('error'):
                        line += f" [ERROR: {item['error']}]"
                    lines.append(line)
                
                return [types.TextContent(type="text", text="\n".join(lines))]
            else:
                # Default: simple flat list
                paths = [item['path'] for item in unique_items]
                return [types.TextContent(type="text", text="\n".join(paths))]
        
    except Exception as e:
        error_metadata = {
            "operation": "file_list_patterns",
            "success": False,
            "error": str(e)
        }
        result = json.dumps({"metadata": error_metadata}, indent=2)
        return [types.TextContent(type="text", text=result)]
