# Multi-Agent Configuration

This directory contains configuration files for the Multi-Agent Manager system.

## File Structure

Each agent is stored in a separate JSON file named using the agent's name converted to lowercase with hyphens instead of spaces:
- Agent name: "My Custom Agent" → File: `my-custom-agent.json`
- Agent name: "Database Handler" → File: `database-handler.json`
- Agent name: "API Monitor" → File: `api-monitor.json`

## Agent File Format

Each agent configuration file is a JSON document with the following structure:

```json
{
  "agent_id": "unique-uuid-identifier",
  "name": "Human Readable Agent Name",
  "module_path": "path/to/monitored/module",
  "available_tools": [
    "tool_name_1",
    "tool_name_2"
  ],
  "description": "Description of the agent's purpose and functionality",
  "created_at": "ISO-8601-timestamp",
  "last_active": "ISO-8601-timestamp"
}
```

## Fields Description

- `agent_id` - Unique UUID identifier for the agent
- `name` - Human readable name (can contain spaces and special characters)
- `module_path` - Path to the module or directory this agent monitors
- `available_tools` - Array of tool names the agent can use (from tool registry)
- `description` - Detailed description of the agent's purpose and responsibilities
- `created_at` - ISO-8601 timestamp when the agent was created
- `last_active` - ISO-8601 timestamp of the agent's last activity

## Configuration Management

### Agent Lifecycle
1. **Load**: Agents loaded from individual JSON files when MCP server starts
2. **Runtime**: Agents exist in server memory during session
3. **Save**: Individual agent files automatically updated when agents are created/modified/removed
4. **Memory**: Conversation history exists only in RAM (lost on restart)

## Important Notes

- Agent files are automatically managed by the `lng_multi_agent_manager` tool
- Do not edit manually - use the MCP tool operations instead
- Each agent has a unique UUID and is associated with a specific module path
- Agent memory (conversation history) is not persisted to disk
- Filename generation automatically converts spaces to hyphens and uses lowercase
