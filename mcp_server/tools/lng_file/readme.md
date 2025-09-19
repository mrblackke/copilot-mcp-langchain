# lng_file - File Operations Tools

Cross-platform tools for reading and writing text files with advanced features and flexible output formats.

## Tools

### lng_file_read
Reads text files with encoding support and optional offset/limit functionality.

**Key Features:**
- **Dual Output Formats**: Plain text (default) or JSON with metadata
- Support for various encodings (UTF-8, ASCII, CP1251, Latin-1, etc.)
- Offset/limit for reading specific line ranges
- Cross-platform path handling (absolute/relative paths)
- Comprehensive error handling with detailed messages
- Unicode support with proper character handling

**Parameters:**
- `file_path` (required): Path to the file to read
- `encoding` (optional): File encoding, default: 'utf-8'
- `offset` (optional): Number of lines to skip from beginning, default: 0
- `limit` (optional): Maximum number of lines to read
- `output_format` (optional): 'text' (default) or 'json'

### lng_file_write  
Writes text content to files with multiple write modes and comprehensive metadata.

**Key Features:**
- **JSON Metadata Response**: Always returns structured operation details
- Three write modes: create (default), overwrite, append
- Automatic directory creation for nested paths
- Support for various encodings (UTF-8, ASCII, CP1251, Latin-1, etc.)
- Detailed operation metadata with timestamps
- Safe file existence checks with mode validation
- Unicode content support

**Parameters:**
- `file_path` (required): Path to the file to write
- `content` (required): Text content to write
- `encoding` (optional): File encoding, default: 'utf-8'
- `mode` (optional): Write mode - 'create', 'overwrite', or 'append'

### lng_file_list
Lists files and directories using multiple glob patterns with flexible filtering and output options.

**Key Features:**
- **Multiple Glob Patterns**: Support for multiple search patterns in one call
- **Pattern Grouping**: Group results by pattern or return deduplicated flat list
- **Multiple Output Formats**: Simple list, detailed view, or JSON with metadata
- Path type options: relative (default) or absolute paths
- Built-in glob support including recursive patterns (`**/*`)
- Type filtering: files only, directories only, or both
- Hidden file inclusion control
- Comprehensive error handling with pattern-specific feedback

**Parameters:**
- `patterns` (required): Array of glob patterns to search for files and directories
- `base_path` (optional): Base directory path for pattern matching, default: current directory (".")
- `group_by_pattern` (optional): Group results by pattern, default: false (flat list with deduplication)
- `path_type` (optional): 'relative' (default) or 'absolute' paths
- `include_directories` (optional): Include directories, default: true
- `include_files` (optional): Include files, default: true
- `show_hidden` (optional): Include hidden files/directories, default: false
- `output_format` (optional): 'list' (default), 'detailed', or 'json'

## Usage Examples

### Reading Files

```bash
# Read entire file (plain text format - default)
python -m mcp_server.run run lng_file_read '{"file_path":"data.txt"}'

# Read entire file (JSON format with metadata)
python -m mcp_server.run run lng_file_read '{"file_path":"data.txt","output_format":"json"}'

# Read with offset and limit
python -m mcp_server.run run lng_file_read '{"file_path":"data.txt","offset":9,"limit":10}'
```

### Writing Files

```bash
# Create new file
python -m mcp_server.run run lng_file_write '{"file_path":"output.txt","content":"Hello World"}'

# Append to existing file
python -m mcp_server.run run lng_file_write '{"file_path":"log.txt","content":"New entry\\n","mode":"append"}'

# Write with Unicode content
python -m mcp_server.run run lng_file_write '{"file_path":"unicode.txt","content":"Hello 🌍!","encoding":"utf-8"}'
```

### Listing Directory Contents

```bash
# List all files and directories in current directory (simple format)
python -m mcp_server.run run lng_file_list '{"patterns":["*"]}'

# List only files with absolute paths  
python -m mcp_server.run run lng_file_list '{"patterns":["*"],"path_type":"absolute","include_directories":false}'

# List Python files recursively
python -m mcp_server.run run lng_file_list '{"patterns":["**/*.py"],"base_path":"src"}'

# Multiple patterns - .py and .md files
python -m mcp_server.run run lng_file_list '{"patterns":["**/*.py","**/*.md"],"base_path":"."}'

# Multiple patterns with grouping by pattern
python -m mcp_server.run run lng_file_list '{"patterns":["src/**/*.py","tests/**/*.py","docs/*.md"],"group_by_pattern":true}'

# Detailed listing with file information
python -m mcp_server.run run lng_file_list '{"patterns":["*"],"base_path":"docs","output_format":"detailed"}'

# JSON format with full metadata
python -m mcp_server.run run lng_file_list '{"patterns":["**/*.log"],"base_path":"logs","output_format":"json"}'
```

## Output Formats

### lng_file_read Output Formats

**Plain Text Format (default)**
```
Line 1 of file
Line 2 of file
Line 3 of file
```

**JSON Format** (when `output_format: "json"`)
```json
{
  "content": "Line 1 of file\nLine 2 of file\nLine 3 of file\n",
  "metadata": {
    "operation": "file_read",
    "file_path": "/path/to/file.txt",
    "encoding": "utf-8",
    "file_size_bytes": 42,
    "lines_count": 3,
    "content_character_count": 39,
    "offset": 0,
    "limit": null,
    "success": true,
    "timestamp": "2025-08-11T12:00:00.000000"
  }
}
```

### lng_file_write Output Format

**Always JSON Response with Metadata**
```json
{
  "metadata": {
    "operation": "file_write",
    "file_path": "/path/to/file.txt",
    "encoding": "utf-8",
    "mode": "create",
    "content_character_count": 25,
    "content_lines_count": 2,
    "file_size_bytes": 25,
    "success": true,
    "timestamp": "2025-08-11T12:00:00.000000"
  }
}
```

### lng_file_list Output Formats

**Simple List Format (default)**
```
file1.txt
file2.py
subdirectory/
file3.md
```

**Detailed Format**
```
Directory listing: /path/to/directory
Total items: 4

     file: file1.txt (1024 bytes)
     file: file2.py (2048 bytes)
directory: subdirectory/
     file: file3.md (512 bytes)
```

**JSON Format (flat list)**
```json
{
  "items": [
    {
      "path": "file1.txt",
      "name": "file1.txt",
      "type": "file",
      "pattern": "*.txt",
      "size": 1024,
      "modified_time": 1691835600.0,
      "permissions": "644",
      "is_hidden": false,
      "absolute_path": "/path/to/directory/file1.txt"
    },
    {
      "path": "subdirectory",
      "name": "subdirectory", 
      "type": "directory",
      "pattern": "*",
      "size": null,
      "modified_time": 1691835700.0,
      "permissions": "755",
      "is_hidden": false,
      "absolute_path": "/path/to/directory/subdirectory"
    }
  ],
  "metadata": {
    "operation": "file_list_patterns",
    "base_path": "/path/to/directory",
    "patterns": ["*.txt", "*"],
    "group_by_pattern": false,
    "path_type": "relative",
    "include_directories": true,
    "include_files": true,
    "show_hidden": false,
    "output_format": "json",
    "total_items": 2,
    "patterns_processed": 2,
    "success": true
  }
}
```

**JSON Format (grouped by pattern)**
```json
{
  "grouped_results": {
    "*.py": ["main.py", "utils.py"],
    "*.txt": ["readme.txt", "config.txt"],
    "docs/*.md": ["docs/api.md", "docs/guide.md"]
  },
  "metadata": {
    "operation": "file_list_patterns",
    "base_path": "/path/to/directory",
    "patterns": ["*.py", "*.txt", "docs/*.md"],
    "group_by_pattern": true,
    "total_items": 6,
    "patterns_processed": 3,
    "success": true
  }
}
```

## Error Handling

Both tools provide detailed error information in JSON format for common scenarios:

### Read Tool Errors
- **File not found**: Returns JSON with error details
- **Permission denied**: JSON error with access information
- **Encoding errors**: JSON with encoding mismatch details
- **Invalid parameters**: JSON with parameter validation errors

### Write Tool Errors  
- **File exists** (create mode): JSON error with conflict details
- **Permission denied**: JSON error with access information
- **Disk space issues**: JSON error with storage details
- **Invalid paths**: JSON error with path validation details
- **Missing parameters**: JSON error with parameter requirements

### Example Error Response
```json
{
  "metadata": {
    "operation": "file_read",
    "file_path": "/nonexistent/file.txt",
    "success": false,
    "error": "File not found: /nonexistent/file.txt",
    "timestamp": "2025-08-11T12:00:00.000000"
  }
}
```
