"""
Test script for multi-agent system

This script demonstrates how to:
1. Create a sub-agent for a specific module
2. Query the sub-agent with questions
3. List and manage sub-agents
"""

import asyncio
import json
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from mcp_server.tools.lng_multi_agent.manager.tool import run_tool

async def test_multi_agent_system():
    """Test the multi-agent system functionality"""
    
    print("=== Multi-Agent System Test ===\n")
    
    # Test 1: Create a sub-agent for the tools directory
    print("1. Creating a sub-agent for lng_file module...")
    create_params = {
        "operation": "create_agent",
        "name": "File Tools Agent",
        "module_path": "mcp_server/tools/lng_file",
        "available_tools": ["lng_file_read", "lng_file_list"],
        "description": "Agent responsible for file manipulation tools - read and list operations"
    }
    
    result = await run_tool("lng_multi_agent_manager", create_params)
    create_response = json.loads(result[0].text)
    
    if create_response.get("success"):
        agent_id = create_response["agent_id"]
        print(f"✅ Agent created successfully with ID: {agent_id}")
        print(f"   Name: {create_response['name']}")
        print(f"   Module: {create_response['module_path']}")
        print(f"   Tools: {create_response['available_tools']}")
    else:
        print(f"❌ Failed to create agent: {create_response.get('error', 'Unknown error')}")
        return
    
    print()
    
    # Test 2: List all agents
    print("2. Listing all agents...")
    list_params = {"operation": "list_agents"}
    result = await run_tool("lng_multi_agent_manager", list_params)
    list_response = json.loads(result[0].text)
    
    if list_response.get("success"):
        agents = list_response["agents"]
        print(f"✅ Found {len(agents)} agent(s):")
        for agent in agents:
            print(f"   - {agent['name']} (ID: {agent['agent_id'][:8]}...)")
            print(f"     Module: {agent['module_path']}")
            print(f"     Tools: {len(agent['available_tools'])} tools")
            print(f"     Last active: {agent['last_active']}")
    else:
        print(f"❌ Failed to list agents: {list_response.get('error', 'Unknown error')}")
    
    print()
    
    # Test 3: Query the agent
    print("3. Querying the agent about its module...")
    query_params = {
        "operation": "query_agent",
        "agent_id": agent_id,
        "question": "What files are in your assigned module? Please list them and briefly describe what each tool does."
    }
    
    result = await run_tool("lng_multi_agent_manager", query_params)
    query_response = json.loads(result[0].text)
    
    if query_response.get("success"):
        print("✅ Agent response:")
        print(f"   Question: {query_response['question']}")
        print(f"   Response: {query_response['response']}")
    else:
        print(f"❌ Failed to query agent: {query_response.get('error', 'Unknown error')}")
    
    print()
    
    # Test 4: Find agent by module path
    print("4. Finding agent by module path...")
    find_params = {
        "operation": "find_agent",
        "module_path": "mcp_server/tools/lng_file"
    }
    
    result = await run_tool("lng_multi_agent_manager", find_params)
    find_response = json.loads(result[0].text)
    
    if find_response.get("success") and find_response.get("agent_id"):
        found_agent_id = find_response["agent_id"]
        print(f"✅ Found agent {found_agent_id[:8]}... for module {find_response['module_path']}")
    else:
        print(f"❌ No agent found for module: {find_response.get('module_path', 'Unknown')}")
    
    print()
    
    # Test 5: Query with a more complex question
    print("5. Asking a more complex question...")
    complex_query_params = {
        "operation": "query_agent",
        "agent_id": agent_id,
        "question": "Can you read the tool.py file from the 'read' subdirectory and explain what the lng_file_read tool does? What are its main parameters?"
    }
    
    result = await run_tool("lng_multi_agent_manager", complex_query_params)
    complex_response = json.loads(result[0].text)
    
    if complex_response.get("success"):
        print("✅ Agent response to complex query:")
        print(f"   Response: {complex_response['response']}")
    else:
        print(f"❌ Failed to run complex query: {complex_response.get('error', 'Unknown error')}")
    
    print()
    
    # Test 6: Clean up - remove the agent
    print("6. Cleaning up - removing the test agent...")
    remove_params = {
        "operation": "remove_agent",
        "agent_id": agent_id
    }
    
    result = await run_tool("lng_multi_agent_manager", remove_params)
    remove_response = json.loads(result[0].text)
    
    if remove_response.get("success"):
        print(f"✅ Agent {agent_id[:8]}... removed successfully")
    else:
        print(f"❌ Failed to remove agent: {remove_response.get('error', 'Unknown error')}")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    asyncio.run(test_multi_agent_system())
