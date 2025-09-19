#!/usr/bin/env python3
"""
Emergency cleanup utility for stuck hotkeys.

This script performs a brute-force cleanup of all registered hotkeys in Windows.
Use this ONLY when the normal hotkey service cleanup doesn't work properly,
such as after daemon crashes or system errors.

Usage: python emergency_cleanup_hotkeys.py
"""

import win32gui

print("🚨 EMERGENCY HOTKEY CLEANUP")
print("This will attempt to unregister ALL hotkeys in the system!")
print("Use only when normal cleanup doesn't work.")
print()

# Try to unregister hotkeys that might be stuck
cleaned_count = 0
for i in range(1, 100000):
    try:
        win32gui.UnregisterHotKey(None, i)
        print(f"✅ Unregistered hotkey ID: {i}")
        cleaned_count += 1
    except:
        pass

print()
print(f"🧹 Emergency cleanup completed!")
print(f"📊 Total hotkeys cleaned: {cleaned_count}")
print()
print("💡 Next time, try using the normal cleanup first:")
print("   python -m mcp_server.run run lng_winapi_hotkey_listener '{\"operation\":\"unregister_all\"}'")
