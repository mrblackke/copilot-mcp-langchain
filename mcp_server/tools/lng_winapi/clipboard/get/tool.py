import mcp.types as types
import json
import win32clipboard
import win32con
import time

async def tool_info() -> dict:
    return {
        "description": """Gets text content from Windows clipboard. Returns the current clipboard text or detailed error information.

CAPABILITIES:
• Unicode text support - Reads both Unicode and ANSI text formats
• Format detection - Automatically detects and reports text format
• Automatic retries - Handles clipboard access conflicts gracefully
• Content analysis - Reports text length and format information

RETURN FORMATS:
• unicode_text: Modern Unicode text (preferred)
• ansi_text: Legacy ANSI text (fallback)
• Error states: Clear error messages when clipboard is empty or inaccessible

USAGE EXAMPLES:
• Basic read: {} (no parameters needed)
• With retries: timeout_attempts=20 (for busy systems)

ERROR HANDLING:
• Empty clipboard detection
• Non-text content handling
• Clipboard access conflict resolution
• Detailed error reporting for troubleshooting""",
        "schema": {
            "type": "object",
            "properties": {
                "timeout_attempts": {
                    "type": "integer",
                    "description": "Number of attempts to open clipboard (default: 10)."
                }
            },
            "required": []
        }
    }

async def run_tool(name: str, arguments: dict) -> list[types.Content]:
    timeout_attempts = arguments.get("timeout_attempts", 10)
    
    try:
        # Try to open clipboard with retries
        opened = False
        last_error = None
        
        for attempt in range(timeout_attempts):
            try:
                win32clipboard.OpenClipboard()
                opened = True
                break
            except Exception as e:
                last_error = str(e)
                if attempt < timeout_attempts - 1:
                    time.sleep(0.1)  # Wait 100ms before retry
                continue
        
        if not opened:
            return [types.TextContent(
                type="text", 
                text=json.dumps({
                    "success": False,
                    "error": f"Failed to open clipboard after {timeout_attempts} attempts. Last error: {last_error}",
                    "content": None
                }, ensure_ascii=False, indent=2)
            )]
        
        try:
            # Check if clipboard has text data
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                try:
                    # Get Unicode text
                    text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                    result = {
                        "success": True,
                        "content": text,
                        "format": "unicode_text",
                        "length": len(text),
                        "debug": {
                            "text_repr": repr(text),
                            "byte_length": len(text.encode('utf-8')),
                            "contains_emoji": any(ord(char) > 0xFFFF for char in text)
                        }
                    }
                except Exception as e:
                    result = {
                        "success": False,
                        "error": f"Error reading Unicode text: {str(e)}",
                        "content": None
                    }
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                try:
                    # Get ANSI text
                    text = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                    if isinstance(text, bytes):
                        text = text.decode('ansi', errors='ignore')
                    result = {
                        "success": True,
                        "content": text,
                        "format": "ansi_text",
                        "length": len(text)
                    }
                except Exception as e:
                    result = {
                        "success": False,
                        "error": f"Error reading ANSI text: {str(e)}",
                        "content": None
                    }
            else:
                result = {
                    "success": False,
                    "error": "Clipboard does not contain text data",
                    "content": None
                }
                
        except Exception as e:
            result = {
                "success": False,
                "error": f"Error accessing clipboard data: {str(e)}",
                "content": None
            }
        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass  # Ignore close errors
            
        return [types.TextContent(
            type="text", 
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text", 
            text=json.dumps({
                "success": False,
                "error": f"Exception occurred: {str(e)}",
                "content": None
            }, ensure_ascii=False, indent=2)
        )]
