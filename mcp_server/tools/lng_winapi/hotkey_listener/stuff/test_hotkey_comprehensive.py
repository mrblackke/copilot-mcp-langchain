#!/usr/bin/env python3
"""
Comprehensive hotkey test - register hotkey and send it in same process.
"""
import win32gui
import win32con
import win32api
import threading
import time
import sys

def test_hotkey_in_process():
    """Test hotkey registration and triggering in same process"""
    hotkey_id = 42001
    vk_code = win32con.VK_F5  # F5 key
    modifiers = 0  # No modifiers
    
    print(f"Testing hotkey registration for F5 (VK_CODE={vk_code})")
    
    # Register hotkey
    try:
        result = win32gui.RegisterHotKey(None, hotkey_id, modifiers, vk_code)
        print(f"RegisterHotKey returned: {result}")
        if result is None:
            print("✅ Hotkey registered successfully")
        else:
            print(f"❌ Registration failed: {result}")
            return
    except Exception as e:
        print(f"❌ Registration exception: {e}")
        return
    
    # Create a thread to send the hotkey after a delay
    def send_hotkey_delayed():
        print("⏳ Waiting 3 seconds before sending F5...")
        time.sleep(3)
        print("📤 Sending F5 key...")
        
        # Send F5 key
        win32api.keybd_event(vk_code, 0, 0, 0)  # Key down
        time.sleep(0.1)
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)  # Key up
        print("✅ F5 key sent")
    
    # Start the sender thread
    sender_thread = threading.Thread(target=send_hotkey_delayed, daemon=True)
    sender_thread.start()
    
    # Message loop to catch the hotkey
    print("🔍 Starting message loop to catch hotkey...")
    start_time = time.time()
    hotkey_caught = False
    
    while time.time() - start_time < 10:  # Wait up to 10 seconds
        try:
            msg = win32gui.PeekMessage(None, win32con.WM_HOTKEY, win32con.WM_HOTKEY, win32con.PM_REMOVE)
            if msg:
                print(f"📨 Got message: {msg}")
                if msg[0] == win32con.WM_HOTKEY and msg[2] == hotkey_id:
                    print(f"🎉 HOTKEY CAUGHT! ID: {msg[2]}")
                    hotkey_caught = True
                    break
        except Exception as e:
            # PeekMessage might fail when no messages
            pass
        
        time.sleep(0.01)  # Small delay to avoid busy waiting
    
    # Cleanup
    try:
        win32gui.UnregisterHotKey(None, hotkey_id)
        print("🧹 Hotkey unregistered")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")
    
    if hotkey_caught:
        print("✅ SUCCESS: Hotkey was successfully caught!")
        return True
    else:
        print("❌ FAILED: Hotkey was not caught")
        return False

if __name__ == "__main__":
    success = test_hotkey_in_process()
    sys.exit(0 if success else 1)
