# Multi-Agent System Demo

This demo shows how to use the multi-agent system for code analysis.

## Scenario: Analyzing the lng_file module

Let's create a specialized agent to analyze file operation tools.

### Step 1: Create a specialized agent

```bash
python -m mcp_server.run run lng_multi_agent_manager '{
  "operation": "create_agent",
  "name": "File Tools Analyst", 
  "module_path": "mcp_server/tools/lng_file",
  "available_tools": ["lng_file_read", "lng_file_list"],
  "description": "Specialized agent for analyzing file manipulation tools and their implementations"
}'
```

This creates an agent that can:
- Read files in the lng_file module
- List directory contents
- Analyze code structure
- Answer questions about file tool implementations

### Step 2: Query the agent

```bash
# Get the agent ID from step 1, then query it:
python -m mcp_server.run run lng_multi_agent_manager '{
  "operation": "query_agent",
  "agent_id": "YOUR_AGENT_ID_HERE", 
  "question": "What are the main tools in this module and what do they do?"
}'
```

### Step 3: Ask more specific questions

```bash
python -m mcp_server.run run lng_multi_agent_manager '{
  "operation": "query_agent",
  "agent_id": "YOUR_AGENT_ID_HERE",
  "question": "Can you read the lng_file_read tool.py file and explain its parameters?"
}'
```

### Step 4: Orchestrator workflow

The orchestrator (Copilot) can:
1. Create multiple specialized agents for different modules
2. Query each agent for information about their domains
3. Collect comprehensive information before making changes
4. Use agent insights to guide implementation decisions

### Example orchestrator questions:

- "What files are in the authentication module?" → Auth Agent
- "How does the database layer work?" → DB Agent  
- "What are the main API endpoints?" → API Agent
- "What UI components do we have?" → Frontend Agent

Then orchestrator synthesizes all responses before implementing changes.

## Benefits

- **Separation of Concerns**: Each agent focuses on one module
- **Parallel Analysis**: Multiple agents can work simultaneously  
- **Memory Persistence**: Agents remember previous conversations
- **Scalable**: Add agents for any new modules
- **Flexible Tools**: Each agent gets only the tools it needs
