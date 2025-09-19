## Info
- These instructions are needed to demonstrate the web interface for MCP tools execution via browser.

## How to ask for demo in chat
Use this case to make demo:
```
Show me demo from file:
Start web-mcp interface for browser-based MCP tools execution.
```

## Important
- Follow instructions to enable `MCP`, then use `MCP` for calling all the tools below. If `MCP` is not available - ask user to run it and stop.
- Workspace is `mcp_server/projects/web-mcp/`.

## Demo Steps

1. **Stop existing webhooks**: Use `lng_batch_run` with `{"pipeline_file": "mcp_server/projects/web-mcp/config/stop_webhooks.json"}`

2. **Start webhook servers**: Use `lng_batch_run` with `{"pipeline_file": "mcp_server/projects/web-mcp/config/start_webhooks.json"}`

3. **Provide user instructions**:
   - Web Interface: http://localhost:8080/
   - Tools Api:     http://localhost:8080/api/tools
   - Execution API: http://localhost:8081/execute
   - Tell user to test the interface in browser

4. **Wait for user confirmation** that they tested the web interface

5. **Stop servers**: Use the same as in step 1