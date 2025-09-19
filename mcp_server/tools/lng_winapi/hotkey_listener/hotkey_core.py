import json
import threading
import time
import logging
import win32api
import win32con
import win32gui
from typing import Dict, Callable, Any
from mcp_server.tools.tool_registry import run_tool as execute_mcp_tool
from mcp_server.logging_config import setup_logging

logger = setup_logging("mcp_server", logging.DEBUG)

# Global storage for active hotkey listeners
_active_listeners: Dict[str, Dict[str, Any]] = {}
_listener_lock = threading.Lock()

# Virtual key code mapping
VK_MAP = {
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46, 'g': 0x47, 'h': 0x48,
    'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50,
    'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54, 'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58,
    'y': 0x59, 'z': 0x5A,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34, '5': 0x35, '6': 0x36, '7': 0x37,
    '8': 0x38, '9': 0x39,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74, 'f6': 0x75, 'f7': 0x76,
    'f8': 0x77, 'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
    'space': 0x20, 'enter': 0x0D, 'tab': 0x09, 'esc': 0x1B, 'escape': 0x1B,
    'backspace': 0x08, 'delete': 0x2E, 'insert': 0x2D, 'home': 0x24, 'end': 0x23,
    'pageup': 0x21, 'pagedown': 0x22, 'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
    'numpad0': 0x60, 'numpad1': 0x61, 'numpad2': 0x62, 'numpad3': 0x63, 'numpad4': 0x64,
    'numpad5': 0x65, 'numpad6': 0x66, 'numpad7': 0x67, 'numpad8': 0x68, 'numpad9': 0x69
}

def parse_hotkey(hotkey_str: str) -> Dict[str, Any]:
    """Parse hotkey string like 'ctrl+shift+f1' into components"""
    hotkey_str = hotkey_str.lower().strip()
    
    # Handle different hotkey formats
    parts = []
    if '+' in hotkey_str:
        parts = [part.strip() for part in hotkey_str.split('+')]
    elif '-' in hotkey_str:
        parts = [part.strip() for part in hotkey_str.split('-')]
    else:
        # Single key
        parts = [hotkey_str]
    
    modifiers = 0
    key_name = None
    
    for part in parts:
        if part in ['ctrl', 'control']:
            modifiers |= win32con.MOD_CONTROL
        elif part in ['shift']:
            modifiers |= win32con.MOD_SHIFT
        elif part in ['alt']:
            modifiers |= win32con.MOD_ALT
        elif part in ['win', 'windows']:
            modifiers |= win32con.MOD_WIN
        else:
            # This should be the main key
            key_name = part
    
    if not key_name or key_name not in VK_MAP:
        raise ValueError(f"Invalid or unsupported key: {key_name}")
    
    return {
        'modifiers': modifiers,
        'vk_code': VK_MAP[key_name],
        'key_name': key_name
    }

class HotkeyListener:
    def __init__(self, hotkey_id: int, hotkey_str: str, tool_name: str, tool_args: dict):
        self.hotkey_id = hotkey_id
        self.hotkey_str = hotkey_str
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.thread = None
        self.stop_event = threading.Event()
        self.registered = False
        
    def start(self):
        """Start the hotkey listener in a separate thread"""
        if self.thread and self.thread.is_alive():
            return False
        
        # Just validate the hotkey format first
        try:
            hotkey_info = parse_hotkey(self.hotkey_str)
            logger.debug(f"Parsed hotkey {self.hotkey_str}: modifiers={hotkey_info['modifiers']}, vk_code={hotkey_info['vk_code']}")
        except Exception as e:
            logger.error(f"Error parsing hotkey {self.hotkey_str}: {e}")
            return False
            
        self.thread = threading.Thread(target=self._listen_thread, daemon=True)
        self.thread.start()
        
        # Wait a bit for the thread to start and register the hotkey
        time.sleep(0.5)
        return True
    
    def stop(self):
        """Stop the hotkey listener"""
        self.stop_event.set()
        if self.registered:
            try:
                win32gui.UnregisterHotKey(None, self.hotkey_id)
                self.registered = False
                logger.info(f"Unregistered hotkey {self.hotkey_id}")
            except Exception as e:
                logger.error(f"Error unregistering hotkey {self.hotkey_id}: {e}")
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
    
    def _listen_thread(self):
        """Thread function that registers hotkey and listens for messages"""
        try:
            # Parse the hotkey
            hotkey_info = parse_hotkey(self.hotkey_str)
            logger.info(f"Parsed hotkey {self.hotkey_str}: modifiers={hotkey_info['modifiers']}, vk_code={hotkey_info['vk_code']}")
            
            # Register the global hotkey - try multiple IDs if needed
            registered_successfully = False
            actual_hotkey_id = self.hotkey_id
            
            for id_offset in range(10):  # Try up to 10 different IDs
                current_id = self.hotkey_id + id_offset
                try:
                    logger.info(f"Attempting to register hotkey {self.hotkey_str} with ID {current_id}, modifiers={hotkey_info['modifiers']}, vk_code={hotkey_info['vk_code']}")
                    
                    success = win32gui.RegisterHotKey(
                        None, 
                        current_id, 
                        hotkey_info['modifiers'], 
                        hotkey_info['vk_code']
                    )
                    
                    logger.info(f"RegisterHotKey returned: {success} (type: {type(success)})")
                    
                    # In pywin32, success is None when registration succeeds, or True
                    if success is None or success is True:
                        registered_successfully = True
                        actual_hotkey_id = current_id
                        self.hotkey_id = current_id  # Update the instance ID
                        logger.info(f"Successfully registered hotkey {self.hotkey_str} with ID {current_id}")
                        break
                    else:
                        logger.warning(f"RegisterHotKey returned failure value: {success}")
                        continue
                    
                except Exception as reg_error:
                    logger.info(f"Failed to register with ID {current_id}: {reg_error}")
                    if "already registered" in str(reg_error).lower():
                        logger.info(f"ID {current_id} already in use, trying next ID...")
                        continue
                    else:
                        logger.error(f"Unexpected error with ID {current_id}: {reg_error}")
                        continue
            
            if not registered_successfully:
                logger.error(f"Failed to register hotkey {self.hotkey_str} after trying multiple IDs")
                return
            
            self.registered = True
            
            # Message loop - wait for hotkey messages
            logger.info("Starting message loop...")
            while not self.stop_event.is_set():
                try:
                    # Use GetMessage to wait for messages (blocking, but more efficient)
                    try:
                        # Check for stop event first
                        if self.stop_event.wait(0.1):  # Wait 100ms for stop event
                            break
                            
                        # Use PeekMessage to check for hotkey messages without busy waiting
                        msg = win32gui.PeekMessage(None, win32con.WM_HOTKEY, win32con.WM_HOTKEY, win32con.PM_REMOVE)
                        if msg and msg[0] != 0:  # Only process non-empty messages
                            # Log only meaningful hotkey messages
                            logger.info(f"Got hotkey message: {msg}")
                            # Message structure: msg[1] is a tuple with (hwnd, message, wParam, lParam, time, pt)
                            # For hotkey: message=WM_HOTKEY, wParam=hotkey_id
                            if len(msg) > 1 and len(msg[1]) > 2:
                                message_type = msg[1][1]  # msg[1][1] is the message type
                                hotkey_id = msg[1][2]     # msg[1][2] is wParam (hotkey ID)
                                
                                if message_type == win32con.WM_HOTKEY and hotkey_id == self.hotkey_id:
                                    logger.debug(f"Hotkey {self.hotkey_str} (ID: {self.hotkey_id}) triggered! Calling tool {self.tool_name}")
                                    self._execute_tool()
                        
                    except Exception as msg_e:
                        # If PeekMessage fails, try to continue with a small delay
                        logger.warning(f"PeekMessage failed: {msg_e}")
                        time.sleep(0.1)
                        continue
                    
                except Exception as e:
                    if not self.stop_event.is_set():
                        logger.error(f"Error in message loop for hotkey {self.hotkey_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in hotkey listener thread for {self.hotkey_str}: {e}")
        finally:
            if self.registered:
                try:
                    win32gui.UnregisterHotKey(None, self.hotkey_id)
                    self.registered = False
                    logger.info(f"Unregistered hotkey {self.hotkey_id} in cleanup")
                except Exception as e:
                    logger.error(f"Error unregistering hotkey {self.hotkey_id} in cleanup: {e}")
    
    def _execute_tool(self):
        """Execute the target tool asynchronously"""
        def run_async():
            try:
                import asyncio
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Debug logging
                logger.debug(f"Executing tool: {self.tool_name}")
                logger.debug(f"Tool arguments: {self.tool_args}")
                logger.debug(f"Tool arguments type: {type(self.tool_args)}")
                
                # Run the tool
                result = loop.run_until_complete(execute_mcp_tool(self.tool_name, self.tool_args))
                logger.debug(f"Tool {self.tool_name} executed successfully. Result: {result}")
                
            except Exception as e:
                logger.error(f"Error executing tool {self.tool_name}: {e}")
                logger.error(f"Exception details: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            finally:
                try:
                    loop.close()
                except:
                    pass
        
        # Run in a separate thread to avoid blocking the message loop
        execution_thread = threading.Thread(target=run_async, daemon=True)
        execution_thread.start()

async def register_hotkey(hotkey: str, tool_name: str, tool_json: dict) -> dict:
    """Регистрирует хоткей"""
    with _listener_lock:
        if hotkey in _active_listeners:
            return {"success": False, "error": f"Hotkey {hotkey} is already registered"}
        
        # Validate hotkey format
        try:
            parse_hotkey(hotkey)
        except ValueError as e:
            return {"success": False, "error": f"Invalid hotkey format: {str(e)}"}
        
        # Generate unique hotkey ID - use range that's less likely to conflict
        import random
        base_id = random.randint(40000, 50000)  # Use higher range to avoid conflicts
        
        hotkey_id = None
        # Try up to 100 different IDs to find a free one
        for i in range(100):
            candidate_id = base_id + i
            if candidate_id > 65000:  # Reset to safe range if too high
                candidate_id = 40000 + i
            
            # Check if this ID is already in use by our listeners
            id_in_use = False
            for existing_hotkey, existing_info in _active_listeners.items():
                if existing_info["hotkey_id"] == candidate_id:
                    id_in_use = True
                    break
            
            if not id_in_use:
                hotkey_id = candidate_id
                break
        
        if hotkey_id is None:
            return {"success": False, "error": "Could not find available hotkey ID - too many hotkeys registered"}
        
        # Create and start the listener
        listener = HotkeyListener(hotkey_id, hotkey, tool_name, tool_json)
        if listener.start():
            # Give the listener thread time to register the hotkey
            time.sleep(1.5)
            
            # Check if the hotkey was successfully registered
            if listener.registered:
                _active_listeners[hotkey] = {
                    "listener": listener,
                    "tool_name": tool_name,
                    "tool_json": tool_json,
                    "hotkey_id": hotkey_id,
                    "registered_at": time.time()
                }
                
                return {
                    "success": True,
                    "message": f"Hotkey {hotkey} registered successfully",
                    "hotkey": hotkey,
                    "tool_name": tool_name,
                    "tool_json": tool_json,
                    "hotkey_id": hotkey_id
                }
            else:
                # Stop the listener since registration failed
                listener.stop()
                return {"success": False, "error": f"Failed to register hotkey {hotkey} - listener thread registration failed"}
        else:
            return {"success": False, "error": f"Failed to start hotkey registration for {hotkey}"}

async def unregister_hotkey(hotkey: str) -> dict:
    """Отменяет регистрацию хоткея"""
    with _listener_lock:
        if hotkey not in _active_listeners:
            return {"success": False, "error": f"Hotkey {hotkey} is not registered"}
        
        # Stop the listener
        listener_info = _active_listeners[hotkey]
        listener_info["listener"].stop()
        del _active_listeners[hotkey]
        
        return {
            "success": True,
            "message": f"Hotkey {hotkey} unregistered successfully",
            "hotkey": hotkey
        }

async def list_hotkeys() -> dict:
    """Показывает активные хоткеи"""
    with _listener_lock:
        active_hotkeys = []
        for hotkey, info in _active_listeners.items():
            active_hotkeys.append({
                "hotkey": hotkey,
                "tool_name": info["tool_name"],
                "tool_json": info["tool_json"],
                "hotkey_id": info["hotkey_id"],
                "registered_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info["registered_at"]))
            })
        
        return {
            "success": True,
            "active_hotkeys": active_hotkeys,
            "total_count": len(active_hotkeys)
        }

async def unregister_all_hotkeys() -> dict:
    """Очищает все хоткеи"""
    with _listener_lock:
        count = len(_active_listeners)
        
        # Stop all listeners
        for hotkey, info in list(_active_listeners.items()):
            info["listener"].stop()
        
        _active_listeners.clear()
        
        return {
            "success": True,
            "message": f"All {count} hotkey listeners unregistered successfully",
            "unregistered_count": count
        }
