# Stuff Directory

This directory contains utility scripts and helper tools for the hotkey listener system.

## Files:

### `emergency_cleanup_hotkeys.py`
Emergency cleanup utility for stuck Windows hotkeys.

**When to use:**
- After daemon crashes or system errors
- When normal cleanup doesn't work: `{"operation": "unregister_all"}`
- Before debugging hotkey issues

**How to use:**
```bash
cd mcp_server/tools/lng_winapi/hotkey_listener/stuff
python emergency_cleanup_hotkeys.py
```

**⚠️ Warning:** This script performs brute-force cleanup of ALL system hotkeys. Use only when necessary.

### `debug_hotkey_simple.py`
Debug utility for testing basic Win32 hotkey functionality.

**When to use:**
- Main hotkey system doesn't work
- Need to isolate Win32 API issues  
- Testing basic hotkey registration
- Learning hotkey implementation

**How to use:**
```bash
cd mcp_server/tools/lng_winapi/hotkey_listener/stuff
python debug_hotkey_simple.py
```

**What it tests:**
- Basic RegisterHotKey API call
- PeekMessage message loop
- Hotkey detection (NUMPAD1)
- Proper cleanup

### `simple_hotkey_test.py`
Simple test script for hotkey registration without complex message loop.

**When to use:**
- Testing different hotkey combinations
- Understanding hotkey ID conflicts
- Basic Win32 API learning

**How to use:**
```bash
cd mcp_server/tools/lng_winapi/hotkey_listener/stuff
python simple_hotkey_test.py
```

**What it tests:**
- Multiple hotkey combinations (F1-F6, Numpad keys)
- Modifier combinations (Ctrl, Shift, Alt, Win)
- Automatic ID conflict resolution
- Registration/unregistration cycle

### `test_hotkey_comprehensive.py`
Comprehensive hotkey test that registers and triggers hotkeys in the same process.

**When to use:**
- Testing complete hotkey workflow
- Debugging message loop issues
- Verifying hotkey detection timing

**How to use:**
```bash
cd mcp_server/tools/lng_winapi/hotkey_listener/stuff
python test_hotkey_comprehensive.py
```

**What it tests:**
- F5 hotkey registration
- Programmatic key sending
- Message loop hotkey detection
- Threading and timing

### `test_send_hotkey.py`
Utility for programmatically sending hotkeys to the system.

**When to use:**
- Testing registered hotkeys
- Simulating user input
- Automated testing scenarios

**How to use:**
```bash
cd mcp_server/tools/lng_winapi/hotkey_listener/stuff
python test_send_hotkey.py <vk_code> [modifiers]
# Example: python test_send_hotkey.py 112 2  # F1 with Ctrl
```

**Parameters:**
- `vk_code`: Virtual key code (e.g., 112 for F1)
- `modifiers`: Optional modifier flags (1=Alt, 2=Ctrl, 4=Shift)

### `test_hotkey_mcp.py`
Test script for hotkey integration with MCP server.

**When to use:**
- Testing MCP server hotkey functionality
- Verifying tool execution on hotkey press
- End-to-end system testing

**How to use:**
```bash
cd mcp_server/tools/lng_winapi/hotkey_listener/stuff
python test_hotkey_mcp.py
```

**What it tests:**
- Hotkey registration via MCP server
- Tool execution on hotkey trigger
- MCP server communication
- Cleanup operations

### `test_direct_tool_call.py`
Test script for direct tool calling mechanism without MCP.

**When to use:**
- Testing tool functionality independently
- Debugging tool execution issues
- Bypassing MCP server for testing

**How to use:**
```bash
cd mcp_server/tools/lng_winapi/hotkey_listener/stuff
python test_direct_tool_call.py
```

**What it tests:**
- Direct tool registry access
- Tool execution without MCP layer
- Parameter passing to tools
- Error handling in tool calls

## Normal Operations (recommended):

### Register hotkey:
```bash
python -m mcp_server.run run lng_winapi_hotkey_listener '{
  "operation": "register",
  "hotkey": "Ctrl+Shift+F4", 
  "tool_name": "lng_count_words",
  "tool_json": {"input_text": "test"}
}'
```

### Cleanup hotkeys:
```bash
python -m mcp_server.run run lng_winapi_hotkey_listener '{"operation":"unregister_all"}'
```
