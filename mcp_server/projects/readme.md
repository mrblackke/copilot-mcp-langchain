First of all please create `work` folder and put there all `json` files of Copilot Telemetry.

Then there are 2 ways of how to get value from this:

- Run in terminal `.\mcp_server\projects\telemetry\run.ps1 -BaseDirectory "work"`

- Open `Github Copilot` in `Agent` mode, choose `Claude Sonnet 4`, enable `MCP` in `.vscode/mcp.json` and ask in chat:
```
Show me demo from file:
Please process all github copilot telemetry data in `work`. 
```