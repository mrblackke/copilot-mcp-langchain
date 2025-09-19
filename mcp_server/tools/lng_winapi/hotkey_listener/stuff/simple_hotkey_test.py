import win32gui
import win32con
import time
import threading

# Simple test for hotkey registration without complex message loop
class SimpleHotkeyTest:
    def __init__(self):
        self.registered_ids = []
    
    def test_registration(self, hotkey_str):
        # Parse hotkey
        parts = hotkey_str.lower().split('+')
        modifiers = 0
        key_name = None
        
        VK_MAP = {
            'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74, 'f6': 0x75,
            'numpad0': 0x60, 'numpad1': 0x61, 'numpad2': 0x62, 'numpad3': 0x63, 'numpad4': 0x64,
            'numpad5': 0x65, 'numpad6': 0x66, 'numpad7': 0x67, 'numpad8': 0x68, 'numpad9': 0x69
        }
        
        for part in parts:
            part = part.strip()
            if part in ['ctrl']:
                modifiers |= win32con.MOD_CONTROL
            elif part in ['shift']:
                modifiers |= win32con.MOD_SHIFT
            elif part in ['alt']:
                modifiers |= win32con.MOD_ALT
            elif part in ['win']:
                modifiers |= win32con.MOD_WIN
            else:
                key_name = part
        
        if key_name not in VK_MAP:
            print(f"Unsupported key: {key_name}")
            return False
        
        vk_code = VK_MAP[key_name]
        
        # Try different IDs until we find one that works
        for hotkey_id in range(40000, 41000):
            try:
                print(f"Trying to register {hotkey_str} with ID {hotkey_id}, modifiers={modifiers}, vk_code={vk_code}")
                result = win32gui.RegisterHotKey(None, hotkey_id, modifiers, vk_code)
                print(f"RegisterHotKey returned: {result} (type: {type(result)})")
                
                # If no exception, registration succeeded
                self.registered_ids.append(hotkey_id)
                print(f"✅ Successfully registered {hotkey_str} with ID {hotkey_id}")
                
                # Test unregistration
                try:
                    win32gui.UnregisterHotKey(None, hotkey_id)
                    self.registered_ids.remove(hotkey_id)
                    print(f"✅ Successfully unregistered {hotkey_str}")
                    return True
                except Exception as unreg_e:
                    print(f"❌ Failed to unregister: {unreg_e}")
                    return False
                    
            except Exception as e:
                if "already registered" in str(e).lower():
                    print(f"ID {hotkey_id} already in use, trying next...")
                    continue
                else:
                    print(f"❌ Unexpected error with ID {hotkey_id}: {e}")
                    continue
        
        print(f"❌ Could not find available ID for {hotkey_str}")
        return False
    
    def cleanup(self):
        for hotkey_id in self.registered_ids[:]:
            try:
                win32gui.UnregisterHotKey(None, hotkey_id)
                print(f"Cleaned up hotkey ID {hotkey_id}")
            except:
                pass
        self.registered_ids.clear()

# Test different hotkeys
test = SimpleHotkeyTest()

test_hotkeys = [
    "numpad1",
    "ctrl+numpad2", 
    "shift+numpad3",
    "alt+numpad4",
    "ctrl+shift+numpad5",
    "f1",
    "ctrl+f2"
]

print("=== Testing Hotkey Registration ===")
for hotkey in test_hotkeys:
    print(f"\n--- Testing {hotkey} ---")
    success = test.test_registration(hotkey)
    if success:
        print(f"🎉 {hotkey} works!")
        break
    else:
        print(f"❌ {hotkey} failed")

test.cleanup()
print("\n=== Test completed ===")
