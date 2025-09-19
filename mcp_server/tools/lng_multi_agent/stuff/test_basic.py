"""
Simple test for multi-agent system - testing only the creation and basic functionality
without LLM calls to avoid connection issues during development
"""

import asyncio
import json
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from mcp_server.tools.lng_multi_agent.manager.tool import run_tool

async def test_basic_functionality():
    """Test basic multi-agent functionality without LLM calls"""
    
    print("=== Multi-Agent System Basic Test ===\n")
    
    # Test 1: Create a sub-agent
    print("1. Creating a sub-agent...")
    create_params = {
        "operation": "create_agent",
        "name": "Test Agent",
        "module_path": "test/module",
        "available_tools": ["lng_file_read"],
        "description": "Test agent for basic functionality"
    }
    
    result = await run_tool("lng_multi_agent_manager", create_params)
    create_response = json.loads(result[0].text)
    
    if create_response.get("success"):
        agent_id = create_response["agent_id"]
        print(f"✅ Agent created successfully with ID: {agent_id}")
    else:
        print(f"❌ Failed to create agent: {create_response.get('error', 'Unknown error')}")
        return
    
    # Test 2: List agents
    print("\n2. Listing all agents...")
    list_params = {"operation": "list_agents"}
    result = await run_tool("lng_multi_agent_manager", list_params)
    list_response = json.loads(result[0].text)
    
    if list_response.get("success"):
        agents = list_response["agents"]
        print(f"✅ Found {len(agents)} agent(s)")
        for agent in agents:
            print(f"   - {agent['name']} (Module: {agent['module_path']})")
    else:
        print(f"❌ Failed to list agents")
    
    # Test 3: Find agent
    print("\n3. Finding agent by module...")
    find_params = {
        "operation": "find_agent", 
        "module_path": "test/module"
    }
    result = await run_tool("lng_multi_agent_manager", find_params)
    find_response = json.loads(result[0].text)
    
    if find_response.get("success") and find_response.get("agent_id"):
        print(f"✅ Found agent: {find_response['agent_id']}")
    else:
        print(f"❌ Agent not found")
    
    # Test 4: Remove agent
    print("\n4. Removing agent...")
    remove_params = {
        "operation": "remove_agent",
        "agent_id": agent_id
    }
    result = await run_tool("lng_multi_agent_manager", remove_params)
    remove_response = json.loads(result[0].text)
    
    if remove_response.get("success"):
        print(f"✅ Agent removed successfully")
    else:
        print(f"❌ Failed to remove agent")
    
    print("\n=== Basic test completed successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
