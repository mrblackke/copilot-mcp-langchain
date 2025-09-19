# Hotkey Listener MCP Tool

A system-wide hotkey listener that automatically triggers other MCP tools when hotkeys are pressed.

## Overview

This tool registers global Windows hotkeys and executes specified MCP tools with custom JSON parameters when the hotkeys are triggered.

## Features

- **Global hotkey registration** - Works across all applications
- **MCP tool integration** - Calls any MCP tool when hotkey is pressed
- **JSON parameter passing** - Pass custom parameters to target tools
- **Multiple hotkey support** - Register multiple hotkeys simultaneously
- **Thread-safe operation** - Each hotkey runs in its own thread

## Operations

### Service Management
```json
{"operation": "start_service"}
{"operation": "stop_service"}
{"operation": "service_status"}
```

### Register Hotkey
```json
{
  "operation": "register",
  "hotkey": "F5",
  "tool_name": "lng_count_words",
  "tool_json": {"input_text": "Hello world"}
}
```

### List Active Hotkeys
```json
{
  "operation": "list"
}
```

### Unregister Hotkey
```json
{
  "operation": "unregister",
  "hotkey": "F5"
}
```

### Unregister All Hotkeys
```json
{
  "operation": "unregister_all"
}
```

## Supported Hotkey Formats

- **Single keys**: `F1`, `F12`, `Space`, `Enter`
- **With modifiers**: `Ctrl+F1`, `Ctrl+Shift+S`, `Alt+Tab`
- **Modifiers**: `Ctrl`/`Control`, `Shift`, `Alt`, `Win`/`Windows`
- **Keys**: `A-Z`, `0-9`, `F1-F12`, function keys, special keys

## Quick Start

### Using MCP Server (Recommended)

#### Start the hotkey service
```bash
python -m mcp_server.run run lng_winapi_hotkey_listener '{\"operation\":\"start_service\"}'
```

#### Register a hotkey
```bash
python -m mcp_server.run run lng_winapi_hotkey_listener '{\"operation\":\"register\",\"hotkey\":\"F7\",\"tool_name\":\"lng_count_words\",\"tool_json\":{\"input_text\":\"test\"}}'
```

#### List active hotkeys
```bash
python -m mcp_server.run run lng_winapi_hotkey_listener '{\"operation\":\"list\"}'
```

#### Stop the service
```bash
python -m mcp_server.run run lng_winapi_hotkey_listener '{\"operation\":\"stop_service\"}'
```

### Using Hotkey Service Directly
```bash
# Start service in background
python hotkey_service.py daemon

# Or start interactive mode
python hotkey_service.py interactive

# Register hotkey via command line
python hotkey_service.py register F5 lng_count_words '{"input_text": "Hello world"}'

# Check service status
python hotkey_service.py status
```

## Dependencies

- **pywin32** - Windows API access for hotkey registration
- **threading** - Multi-threaded hotkey listeners
- **MCP framework** - Tool registry and execution

## Architecture

1. **HotkeyListener Class** - Manages individual hotkey registration and message loop
2. **Windows Message Loop** - Captures `WM_HOTKEY` messages using `PeekMessage`
3. **Thread Pool** - Each hotkey runs in separate thread for non-blocking operation
4. **Tool Registry Integration** - Dynamically calls registered MCP tools

## Technical Notes

- Uses Win32 `RegisterHotKey` API for system-wide hotkey registration
- Message loop filters for `WM_HOTKEY` (786) messages
- Automatic hotkey ID management to avoid conflicts
- Proper cleanup with `UnregisterHotKey` on shutdown

## Example Use Cases

- **Text processing**: Press F5 to count words in clipboard
- **Calculator**: Press Ctrl+C to perform calculations
- **Screenshot**: Press F12 to take and save screenshots
- **AI queries**: Press Ctrl+Q to ask questions to LLM tools
- **Translation**: Press Ctrl+Shift+Alt+F11 to translate clipboard text via batch pipeline

### Complex Pipeline Example
```bash
# Auto-translate clipboard Russian text to English
python -m mcp_server.run run lng_winapi_hotkey_listener '{\"operation\":\"register\",\"hotkey\":\"ctrl+shift+alt+f11\",\"tool_name\":\"lng_batch_run\",\"tool_json\":{\"pipeline\":[{\"tool\":\"lng_winapi_clipboard_get\",\"params\":{},\"output\":\"clipboard_text\"},{\"tool\":\"lng_llm_prompt_template\",\"params\":{\"command\":\"use\",\"template_name\":\"translate_to_en_b2\",\"text\":\"{! clipboard_text.content || clipboard_text.unicode_text !}\"},\"output\":\"translated_text\"},{\"tool\":\"lng_winapi_clipboard_set\",\"params\":{\"text\":\"{! translated_text !}\"},\"output\":\"final_result\"}],\"final_result\":\"{! translated_text !}\"}}'
```

## Troubleshooting

- **Hotkey conflicts**: Use uncommon combinations like `Ctrl+Shift+Alt+F11`
- **Registration fails**: Check if hotkey is already used by another application
- **Service not responding**: Restart with `stop_service` then `start_service`
