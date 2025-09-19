# Multi-Agent System

This module implements a multi-agent system for LangChain-based code analysis and management.

## Architecture

### Components

1. **MultiAgentManager**: Central orchestrator that manages sub-agents
2. **SubAgent**: Individual agents responsible for specific modules/directories
3. **SubAgentMemory**: Memory management using LangChain's ConversationSummaryBufferMemory
4. **ToolWrapper**: Adapter to use MCP tools as LangChain tools

### Key Features

- **Module Delegation**: Each sub-agent is assigned to monitor specific modules/directories
- **Tool Integration**: Sub-agents can use any tools from the tool_registry.py
- **Memory Management**: Conversations are summarized and stored for context
- **Asynchronous Processing**: Full async support for concurrent agent operations
- **Persistent Configuration**: Agent configs saved to multi_agent_configs.json

### Usage

#### Creating a Sub-Agent

```json
{
  "operation": "create_agent",
  "name": "Frontend Agent",
  "module_path": "/src/components",
  "available_tools": ["lng_file_read", "lng_file_list"],
  "description": "Handles React component analysis"
}
```

#### Querying a Sub-Agent

```json
{
  "operation": "query_agent", 
  "agent_id": "agent-uuid-here",
  "question": "What files are in this module and what do they do?"
}
```

#### Listing All Agents

```json
{
  "operation": "list_agents"
}
```

### Orchestrator Instructions

When working with this system, the main orchestrator (Copilot) should:
1. Never directly access files in delegated modules
2. Always use sub-agents for research and analysis
3. Collect information from multiple sub-agents before making changes
4. Only directly access files when implementing final changes

### Memory Strategy

- Uses ConversationSummaryBufferMemory with 2000 token limit
- Automatically summarizes older conversations to maintain context
- Stores question-answer pairs for reference
- KISS approach - no RAG, just conversation summaries

### Available Tools

Sub-agents can use any tools from tool_registry.py, commonly:
- `lng_file_read` - Read file contents
- `lng_file_list` - List directory contents  
- `lng_file_write` - Write files (future feature)

### Configuration Storage

Agent configurations are persisted in `mcp_server/config/multi_agent/agents.json`:

```json
{
  "agents": [
    {
      "agent_id": "uuid",
      "name": "Agent Name", 
      "module_path": "/path/to/module",
      "available_tools": ["tool1", "tool2"],
      "description": "Agent purpose",
      "created_at": "2025-01-01T00:00:00",
      "last_active": "2025-01-01T00:00:00"
    }
  ]
}
```

## Agent Lifecycle & Memory Management

### Agent Lifecycle

1. **Loading**: Agents are loaded from `agents.json` when MultiAgentManager initializes (on first MCP server access)
2. **Storage**: Agents remain in MCP server memory (`self.agents` dictionary)
3. **Activation**: LLM and LangChain agent are triggered only when `query_agent` is called
4. **Persistence**: Agent configurations are automatically saved to disk when modified

### Memory Behavior

**⚠️ Important Memory Characteristics:**

- **Runtime Memory Only**: Agent conversation history exists only in MCP server RAM
- **No Disk Persistence**: Memory is lost when MCP server restarts
- **Window Memory**: Uses `ConversationBufferWindowMemory` (keeps last 10 interactions)
- **Session-Based**: Each agent maintains memory during MCP server session

### Configuration Management

**Clearing Agents:**
```json
{
  "agents": []
}
```
Setting `agents.json` to empty array removes all agents on next MCP server restart.

**Current vs Persisted State:**
- Agents in memory may differ from `agents.json` until server restart
- Use `list_agents` to see current active agents
- Configuration changes are immediately saved to disk

### Memory Persistence (Future Enhancement)

To implement persistent memory across restarts:
1. Save conversation history to dedicated files
2. Load memory during agent initialization  
3. Update memory files after each interaction

**Current Implementation:**
- Memory exists only during MCP server session
- Restart = fresh memory for all agents
- Focus on stateless, summary-based interactions
