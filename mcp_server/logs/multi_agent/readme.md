# Multi-Agent Conversation Logs

This folder (`mcp_server/logs/multi_agent/`) contains conversation logs between the user and sub-agents of the multi-agent management system.

## Log Structure

Each sub-agent creates its own log file with a name in the format:
```
{agent_name}_{agent_id_8chars}.log
```

Where:
- `agent_name` - agent name (spaces replaced with underscores)
- `agent_id_8chars` - first 8 characters of the agent's UUID

## Entry Format

### Entry Types:

1. **USER:** - Question from user
2. **AGENT:** - Agent response  
3. **TOOL_USED:** - Tool that was used
4. **TOOL_PARAMS:** - Tool parameters (JSON)
5. **TOOL_RESULT:** - Tool execution result
6. **ERROR:** - Errors during operation

### Example log file:
```
2025-08-14 15:30:45 - INFO - === Started conversation with agent Frontend_Agent (ID: a1b2c3d4) ===
2025-08-14 15:30:46 - INFO - USER: What files are in the /src/components directory?
2025-08-14 15:30:46 - INFO - TOOL_USED: lng_file_list
2025-08-14 15:30:46 - INFO - TOOL_PARAMS: {
  "path": "/src/components"
}
2025-08-14 15:30:47 - INFO - TOOL_RESULT: Found 5 files: Button.tsx, Modal.tsx, Header.tsx...
2025-08-14 15:30:47 - INFO - AGENT: In the /src/components directory found the following React component files: Button.tsx, Modal.tsx, Header.tsx...
2025-08-14 15:35:20 - INFO - === Ended conversation with agent Frontend_Agent ===
```

## Logging Features

- Logs are written in UTF-8 encoding
- Tool results are truncated to 500 characters for readability
- Each agent maintains an independent log
- Time is recorded in YYYY-MM-DD HH:MM:SS format

## Log Management

- Logs are created automatically when an agent is created
- When an agent is removed, the session end is logged
- Old log files are not automatically deleted
