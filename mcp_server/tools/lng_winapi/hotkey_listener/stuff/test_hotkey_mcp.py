#!/usr/bin/env python3
"""Test hotkey listener with MCP server"""

import subprocess
import sys
import time
import json

def test_hotkey_registration():
    """Test registering a hotkey and triggering it"""
    
    print("🧪 Testing hotkey registration with MCP server...")
    
    # Prepare JSON parameter
    json_param = json.dumps({"input_text": "test 123 hotkey works"})
    
    # Test registration
    try:
        # Use PowerShell with single quotes around JSON to avoid escaping issues
        powershell_cmd = f"""& C:\\Java\\CopipotTraining\\hello-langchain\\.virtualenv\\Scripts\\Activate.ps1; python -m mcp_server.run run lng_winapi_hotkey_listener register "F5" "lng_count_words" '{json_param}'"""
        
        cmd = ["powershell", "-Command", powershell_cmd]
        
        print(f"🚀 Running PowerShell command: {powershell_cmd}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        print(f"📤 Exit code: {result.returncode}")
        if result.stdout:
            print(f"📜 STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"❗ STDERR:\n{result.stderr}")
            
        if result.returncode == 0:
            print("✅ Hotkey registration successful!")
            
            print("\n🎯 Now press F5 key to test the hotkey...")
            print("⏳ Waiting 10 seconds for you to press F5...")
            time.sleep(10)
            
            # Test listing hotkeys
            list_cmd = [sys.executable, "-m", "mcp_server.run", "run", "lng_winapi_hotkey_listener", "list"]
            list_result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=5)
            print(f"\n📋 Active hotkeys:\n{list_result.stdout}")
            
            # Cleanup
            cleanup_cmd = [sys.executable, "-m", "mcp_server.run", "run", "lng_winapi_hotkey_listener", "unregister_all"]
            cleanup_result = subprocess.run(cleanup_cmd, capture_output=True, text=True, timeout=5)
            print(f"\n🧹 Cleanup result:\n{cleanup_result.stdout}")
            
        else:
            print("❌ Hotkey registration failed!")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out")
        return False
    except Exception as e:
        print(f"💥 Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_hotkey_registration()
