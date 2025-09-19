#!/usr/bin/env python3
"""
Test the tool calling mechanism directly
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к mcp_server в sys.path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.tools.tool_registry import run_tool

async def test_direct_call():
    """Test calling lng_count_words directly"""
    print("🧪 Testing direct tool call...")
    
    tool_name = "lng_count_words"
    tool_args = {"input_text": "Testing direct tool call with multiple words"}
    
    print(f"Tool name: {tool_name}")
    print(f"Tool args: {tool_args}")
    print(f"Tool args type: {type(tool_args)}")
    
    try:
        result = await run_tool(tool_name, tool_args)
        print(f"✅ Success! Result: {result}")
        
        if result and len(result) > 0:
            print(f"📊 Result text: {result[0].text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_direct_call())
