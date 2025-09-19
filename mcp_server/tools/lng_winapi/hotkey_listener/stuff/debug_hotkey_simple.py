#!/usr/bin/env python3
"""
Debug utility for testing basic hotkey registration without threading.

This script helps diagnose Win32 API hotkey issues by testing the most basic
hotkey registration and message loop functionality without the complexity
of the main system.

Usage: python debug_hotkey_simple.py

What it tests:
- Basic RegisterHotKey API call
- PeekMessage message loop
- Hotkey detection
- Proper cleanup

Use this when:
- Main hotkey system doesn't work
- Need to isolate Win32 API issues
- Testing basic hotkey functionality
- Learning hotkey implementation
"""
import win32gui
import win32con
import time
import sys

def test_simple_registration():
    """Test simple hotkey registration without threading complexity"""
    print("🔧 DEBUG: Testing simple hotkey registration...")
    print("=" * 50)
    
    hotkey_id = 42000
    vk_code = win32con.VK_NUMPAD1  # Numpad1
    modifiers = 0  # No modifiers
    
    print(f"📋 Registering hotkey:")
    print(f"   ID: {hotkey_id}")
    print(f"   VK_CODE: {vk_code} (VK_NUMPAD1)")
    print(f"   Modifiers: {modifiers} (none)")
    print()
    
    try:
        # Try to register
        result = win32gui.RegisterHotKey(None, hotkey_id, modifiers, vk_code)
        print(f"✅ RegisterHotKey returned: {result} (type: {type(result)})")
        
        if result is None:
            print("🎉 Registration successful (None means success in pywin32)")
            
            # Test if it's really registered by trying to register the same combination again
            try:
                test_result = win32gui.RegisterHotKey(None, hotkey_id + 1, modifiers, vk_code)
                print(f"🧪 Test registration returned: {test_result}")
                if test_result is None:
                    print("❌ ERROR: Test registration also succeeded - this shouldn't happen!")
                    win32gui.UnregisterHotKey(None, hotkey_id + 1)
                else:
                    print("✅ Good: Test registration failed as expected")
            except Exception as test_e:
                print(f"✅ Test registration failed as expected: {test_e}")
            
            # Try to listen for a few seconds
            print()
            print("👂 Listening for NUMPAD1 hotkey for 5 seconds...")
            print("   Press NUMPAD1 to test!")
            start_time = time.time()
            
            while time.time() - start_time < 5:
                try:
                    msg = win32gui.PeekMessage(None, 0, 0, win32con.PM_REMOVE)
                    if msg:
                        if msg[0] == win32con.WM_HOTKEY and msg[2] == hotkey_id:
                            print(f"🎉 HOTKEY PRESSED! Message: {msg}")
                        win32gui.TranslateMessage(msg)
                        win32gui.DispatchMessage(msg)
                    time.sleep(0.01)
                except Exception as e:
                    # PeekMessage might fail if no messages
                    time.sleep(0.01)
                    continue
            
            print()
            print("🧹 Unregistering hotkey...")
            win32gui.UnregisterHotKey(None, hotkey_id)
            print("✅ Test completed successfully")
            
        else:
            print(f"❌ Registration failed with result: {result}")
            
    except Exception as e:
        print(f"❌ Registration failed with exception: {e}")
        print("💡 This might indicate a system-level issue with hotkey API")

if __name__ == "__main__":
    print("🚀 Win32 Hotkey Debug Utility")
    print("This tool tests basic hotkey functionality")
    print()
    test_simple_registration()
