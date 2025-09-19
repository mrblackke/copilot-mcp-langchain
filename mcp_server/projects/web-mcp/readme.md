# MCP Tools Web Interface

A web interface for MCP (Model Context Protocol) tools, providing universal browser-based access to all available MCP tools.

## Overview

This project creates a web interface that allows users to interact with MCP tools through a browser without needing an IDE. It provides an additional access method for MCP tools:

1. **Terminal** - Direct command-line usage
2. **MCP Protocol** - Through MCP-enabled IDEs and clients  
3. **Pipeline** - Via `lng_batch_run` tool
4. **Web Interface** - Universal browser-based access ⬅️ **This project**

## Features

- **Universal Tool Access** - Execute any MCP tool through web browser
- **Daemon Mode** - Servers run in background with automatic restart
- **Auto Virtual Environment** - Activates Python virtualenv automatically
- **Multi-port Architecture** - Static web (8080) + Execution API (8081)
- **Force Stop** - Emergency process termination for stuck servers
- **Pipeline Integration** - Uses `lng_webhook_server` with pipeline execution
- **Cross-platform** - Works from any directory on Windows/Linux/macOS
- **Simple Management** - One script for start/stop/force-stop operations

## Quick Start

### Prerequisites

- Python MCP server with activated virtual environment
- All MCP tools installed and configured
- Modern web browser (Chrome, Firefox, Edge with ES6+ support)

### Running the Web Interface

1. **Start the server:**
   ```powershell
   .\mcp_server\projects\web-mcp\run.ps1
   ```
   or just:
   ```powershell
   .\mcp_server\projects\web-mcp\run.ps1 start
   ```

2. **Open your browser:**
   - Web Interface: http://localhost:8080/
   - Tools Api:     http://localhost:8080/api/tools
   - Execution API: http://localhost:8081/execute

3. **Stop the server:**
   ```powershell
   .\mcp_server\projects\web-mcp\run.ps1 stop
   ```

4. **Force stop (if processes stuck):**
   ```powershell
   .\mcp_server\projects\web-mcp\run.ps1 force-stop
   ```

## API Endpoints

### Web Interface (Port 8080)
- `GET /webhook` - Main webhook endpoint for web interface

### Execution API (Port 8081)
- `POST /execute` - Execute any MCP tool
  ```json
  {
    "tool": "lng_count_words",
    "params": {"input_text": "Hello world"}
  }
  ```

## Management Commands

All operations use the simplified `run.ps1` script:

```powershell
# Start servers (with auto-stop existing)
.\mcp_server\projects\web-mcp\run.ps1
# or explicitly
.\mcp_server\projects\web-mcp\run.ps1 start

# Stop gracefully via MCP pipelines
.\mcp_server\projects\web-mcp\run.ps1 stop

# Force kill processes on ports 8080/8081
.\mcp_server\projects\web-mcp\run.ps1 force-stop
```

**Script Features:**
- Works from any directory
- Auto-activates virtual environment
- Uses MCP pipelines for graceful start/stop
- Emergency force-stop with process termination

## Configuration Files

### Pipeline Configurations
- `config/start_webhooks.json` - Pipeline to start both webhook servers
- `config/stop_webhooks.json` - Pipeline to stop both webhook servers
- `config/get_static.json` - Static web interface server config (port 8080)
- `config/execute_tool.json` - Tool execution API server config (port 8081)

### Customization
Edit the config files to customize:
- **Ports**: Default 8080 (web) and 8081 (API)
- **Host binding**: `localhost` for local only, `0.0.0.0` for network access
- **Pipeline behavior**: Custom response formats and error handling

## Project Structure

```
web-mcp/
├── config/
│   ├── start_webhooks.json    # Pipeline to start servers
│   ├── stop_webhooks.json     # Pipeline to stop servers
│   ├── get_static.json        # Web interface server config
│   └── execute_tool.json      # Tool execution API config
├── readme.md                  # This documentation
└── run.ps1                    # Management script
```

## Technical Implementation

- **Backend**: `lng_webhook_server` with pipeline integration
- **Architecture**: Webhook-based API with MCP tool execution
- **Management**: PowerShell script with cross-platform paths
- **Process Control**: Native OS commands (`netstat`, `taskkill`) for reliable process management

## Troubleshooting

### Servers Won't Start
```powershell
# Check if ports are occupied
netstat -ano | findstr ":8080"
netstat -ano | findstr ":8081"

# Force stop any processes
.\mcp_server\projects\web-mcp\run.ps1 force-stop
```

### Force Stop Not Working
- Ensure you're running as Administrator (if needed)
- Check if virtual environment is properly activated
- Verify PowerShell execution policy allows scripts

### Can't Access from Network
- Change `bind_host` to `"0.0.0.0"` in config files
- Check firewall settings
- Verify correct IP address and ports

## Related Documentation

- MCP server documentation in `mcp_server/instructions/` folder
- Tool testing guide: `mcp_server/instructions/testing-tool.agent.md`