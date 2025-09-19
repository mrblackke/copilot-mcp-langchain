- To restart the MCP server, you can use the following command:
  + on Windows: `Get-Process python* | Where-Object { $_.ProcessName -like "*python*" } | Stop-Process -Force`
  + on Linux: `pkill -f python`
- Then just call any MCP tool - server will start automatically.
- Don't run the MCP server manually with `python -m mcp_server.run`.
- If something went wrong, ask me to enable it manually in the `.vscode/mcp.json` file. There are buttons for that. Then wait for my confirmation.