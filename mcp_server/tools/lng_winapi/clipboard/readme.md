# Windows Clipboard Tools

This group contains tools for interacting with the Windows clipboard system.

## Tools

### `lng_winapi_clipboard_get`
Reads text content from the Windows clipboard with support for Unicode and ANSI formats.

### `lng_winapi_clipboard_set`  
Writes text content to the Windows clipboard with full Unicode support including emojis.

## Features

- **Unicode Support**: Full support for international characters and emojis
- **Error Handling**: Robust error handling with detailed error messages
- **Retry Mechanism**: Automatic retries for clipboard access conflicts
- **Format Detection**: Automatic detection of text formats (Unicode/ANSI)

## Dependencies

These tools use the `pywin32` package which is included in the parent `lng_winapi` dependencies.

## Usage Examples

```bash
# Set text to clipboard
python -m mcp_server.run run lng_winapi_clipboard_set '{"text":"Hello World! 🌍"}'

# Get text from clipboard  
python -m mcp_server.run run lng_winapi_clipboard_get '{}'

# Batch operation - set then get
python -m mcp_server.run batch lng_winapi_clipboard_set '{"text":"Test"}' lng_winapi_clipboard_get '{}'
```
