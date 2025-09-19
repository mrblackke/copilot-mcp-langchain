#!/usr/bin/env python3
"""
Test hotkey triggering programmatically.
"""
import win32api
import win32con
import time
import sys

def send_hotkey(vk_code, modifiers=0):
    """Send a hotkey programmatically"""
    print(f"Sending hotkey with VK_CODE={vk_code}, modifiers={modifiers}")
    
    # Press modifier keys first
    if modifiers & win32con.MOD_CONTROL:
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        print("Ctrl pressed")
    if modifiers & win32con.MOD_SHIFT:
        win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
        print("Shift pressed")
    if modifiers & win32con.MOD_ALT:
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        print("Alt pressed")
    
    # Press the main key
    win32api.keybd_event(vk_code, 0, 0, 0)
    print(f"Key {vk_code} pressed")
    time.sleep(0.1)
    
    # Release the main key
    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
    print(f"Key {vk_code} released")
    
    # Release modifier keys
    if modifiers & win32con.MOD_ALT:
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        print("Alt released")
    if modifiers & win32con.MOD_SHIFT:
        win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
        print("Shift released")
    if modifiers & win32con.MOD_CONTROL:
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        print("Ctrl released")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_send_hotkey.py <vk_code> [modifiers]")
        print("Example: python test_send_hotkey.py 112 2  # F1 with Ctrl (MOD_CONTROL=2)")
        sys.exit(1)
    
    vk_code = int(sys.argv[1])
    modifiers = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    print(f"Waiting 3 seconds before sending hotkey...")
    time.sleep(3)
    
    send_hotkey(vk_code, modifiers)
    print("Hotkey sent!")
    time.sleep(1)
