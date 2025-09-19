# Hotkey Listener Test Instructions

## Overview
This file contains step-by-step instructions to test the complete hotkey listener workflow for automatic translation functionality.

## Prerequisites
- Virtual environment activated
- MCP server configured
- LLM provider (OpenAI/Azure) configured in .env

## Test Workflow

### Step 1: Stop any running service
**Purpose:** Ensure clean state for testing
```bash
python -m mcp_server.run run lng_winapi_hotkey_listener '{\"operation\":\"stop_service\"}'
```
**Expected:** `{"success": true, "message": "Service stopped successfully"}` or service not running

### Step 2: Verify service is stopped
**Purpose:** Confirm service is not running
```bash
python -m mcp_server.run run lng_winapi_hotkey_listener '{\"operation\":\"service_status\"}'
```
**Expected:** `{"success": true, "running": false, "message": "Service is not running"}`

### Step 3: Start the hotkey service
**Purpose:** Launch the background daemon
```bash
python -m mcp_server.run run lng_winapi_hotkey_listener '{\"operation\":\"start_service\"}'
```
**Expected:** `{"success": true, "message": "Hotkey service started successfully", "pid": XXXX}`

### Step 4: Create translation prompt template
**Purpose:** Set up LLM template for Russian to English translation
```bash
python -m mcp_server.run run lng_llm_prompt_template '{\"command\":\"save\",\"template_name\":\"translate_to_en_b2\",\"template\":\"Translate the following Russian text to English at B2 level. Return only the translated text without any explanations or metadata:\\n\\n{text}\"}'
```
**Expected:** `Prompt template 'translate_to_en_b2' saved successfully`

### Step 5: Register translation hotkey
**Purpose:** Register Ctrl+Shift+Alt+F11 for automatic translation pipeline
```bash
python -m mcp_server.run run lng_winapi_hotkey_listener '{\"operation\":\"register\",\"hotkey\":\"ctrl+shift+alt+f11\",\"tool_name\":\"lng_batch_run\",\"tool_json\":{\"pipeline\":[{\"tool\":\"lng_winapi_clipboard_get\",\"params\":{},\"output\":\"clipboard_text\"},{\"tool\":\"lng_llm_prompt_template\",\"params\":{\"command\":\"use\",\"template_name\":\"translate_to_en_b2\",\"text\":\"{! clipboard_text.content || clipboard_text.unicode_text !}\"},\"output\":\"translated_text\"},{\"tool\":\"lng_winapi_clipboard_set\",\"params\":{\"text\":\"{! translated_text !}\"},\"output\":\"final_result\"}],\"final_result\":\"{! translated_text !}\"}}'
```
**Expected:** `{"success": true, "message": "Hotkey ctrl+shift+alt+f11 registered successfully", "hotkey_id": XXXX}`

### Step 6: Verify hotkey registration
**Purpose:** Confirm hotkey is active and properly configured
```bash
python -m mcp_server.run run lng_winapi_hotkey_listener '{\"operation\":\"list\"}'
```
**Expected:** One active hotkey with correct pipeline configuration

### Step 7: Prepare test text
**Purpose:** Place Russian text in clipboard for translation
```bash
python -m mcp_server.run run lng_winapi_clipboard_set '{\"text\":\"Давайте протестируем наш автоматический переводчик через хоткей\"}'
```
**Expected:** `{"success": true, "message": "Text successfully copied to clipboard"}`

### Step 8: Verify test text in clipboard
**Purpose:** Confirm Russian text is ready for translation
```bash
python -m mcp_server.run run lng_winapi_clipboard_get '{}'
```
**Expected:** `{"success": true, "content": "Давайте протестируем наш автоматический переводчик через хоткей"}`

### Step 9: Manual hotkey trigger (Human action)
**Purpose:** Test the actual hotkey functionality
**Action:** Press `Ctrl+Shift+Alt+F11` physically on keyboard
**Wait:** 5-10 seconds for LLM processing

### Step 10: Verify translation result
**Purpose:** Check if translation completed successfully
```bash
python -m mcp_server.run run lng_winapi_clipboard_get '{}'
```
**Expected:** `{"success": true, "content": "Let's test our automatic translator through a hotkey."}`
**Validation:** Content should be English translation, not Russian original

### Step 11: Test with different Russian text
**Purpose:** Verify repeatability
```bash
python -m mcp_server.run run lng_winapi_clipboard_set '{\"text\":\"Система работает корректно и готова к использованию\"}'
```
**Action:** Press `Ctrl+Shift+Alt+F11` again
**Check result:**
```bash
python -m mcp_server.run run lng_winapi_clipboard_get '{}'
```
**Expected:** English translation of the new text

### Step 12: Clean up (Optional)
**Purpose:** Stop service after testing
```bash
python -m mcp_server.run run lng_winapi_hotkey_listener '{\"operation\":\"unregister_all\"}'
python -m mcp_server.run run lng_winapi_hotkey_listener '{\"operation\":\"stop_service\"}'
```

## Success Criteria

### ✅ Test passes if:
1. Service starts and stops cleanly
2. Hotkey registers without conflicts
3. Russian text gets translated to English
4. Only clean translated text appears in clipboard (no JSON metadata)
5. System works repeatedly with different texts

### ❌ Test fails if:
1. Service fails to start/stop
2. Hotkey registration returns errors
3. Translation doesn't occur after hotkey press
4. Clipboard contains JSON metadata instead of clean text
5. LLM errors or timeouts

## Troubleshooting

### Common Issues:
- **Hotkey conflicts:** Try alternative combinations like `ctrl+shift+alt+f12`
- **LLM timeouts:** Check .env configuration and network connectivity
- **Service won't stop:** Use task manager to kill python.exe processes
- **Pipeline errors:** Verify all tools are available and templates exist

## Expected Timeline
- **Setup (Steps 1-6):** 1-2 minutes
- **Translation test:** 10-15 seconds per test
- **Cleanup:** 30 seconds

## Notes
- Test requires active internet connection for LLM
- Windows-specific functionality (tested on Windows 10/11)
- Hotkey works globally across all applications
- Service persists until manually stopped
