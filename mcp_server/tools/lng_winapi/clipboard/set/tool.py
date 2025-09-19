import mcp.types as types
import json
import win32clipboard
import win32con
import time

async def tool_info() -> dict:
    return {
        "description": """Sets text content to Windows clipboard. Saves the provided text to clipboard and returns success status.

CAPABILITIES:
• Unicode text support - Full Unicode character support including emojis
• Automatic retries - Handles clipboard access conflicts with retry mechanism
• Error handling - Detailed error reporting for troubleshooting
• Text length tracking - Reports the length of text being saved

USAGE EXAMPLES:
• Basic text: text="Hello World"
• Unicode text: text="Привет! 🌍"
• Large text: Automatically handles large text blocks
• With retries: timeout_attempts=20 (for busy systems)

ERROR HANDLING:
• Clipboard access conflicts are handled with automatic retries
• Clear error messages for troubleshooting
• Success/failure status reporting""",
        "schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text content to save to clipboard."
                },
                "timeout_attempts": {
                    "type": "integer",
                    "description": "Number of attempts to open clipboard (default: 10)."
                }
            },
            "required": ["text"]
        }
    }

async def run_tool(name: str, arguments: dict) -> list[types.Content]:
    text = arguments.get("text", "")
    timeout_attempts = arguments.get("timeout_attempts", 10)
    
    # Debug information
    debug_info = {
        "input_text_length": len(text),
        "input_text_repr": repr(text),
        "input_text_bytes": len(text.encode('utf-8'))
    }
    
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
                    "text_length": len(text),
                    "debug": debug_info
                }, ensure_ascii=False, indent=2)
            )]
        
        try:
            # Clear clipboard
            win32clipboard.EmptyClipboard()
            
            # Set text to clipboard with explicit Unicode format
            win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
            
            # Verify the text was set correctly by reading it back
            verification_text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            
            result = {
                "success": True,
                "message": "Text successfully copied to clipboard",
                "text_length": len(text),
                "format": "unicode_text",
                "debug": debug_info,
                "verification": {
                    "length_match": len(text) == len(verification_text),
                    "content_match": text == verification_text,
                    "retrieved_length": len(verification_text)
                }
            }
                        
        except Exception as e:
            result = {
                "success": False,
                "error": f"Error setting clipboard data: {str(e)}",
                "text_length": len(text),
                "debug": debug_info
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
                "text_length": len(text),
                "debug": debug_info
            }, ensure_ascii=False, indent=2)
        )]
