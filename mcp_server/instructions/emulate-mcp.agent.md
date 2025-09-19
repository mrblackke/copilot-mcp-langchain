If there is no MCP enabled, follow instructions:
- Open a terminal and run in background: 
  `python mcp_server/proxy.py`
- Get list of available tools:
  `python mcp_server/execute.py list
- Deside which tool to use by user prompt and run (for example):
  `python mcp_server/execute.py exec lng_count_words --params '{\"input_text\": \"Hello world this is a test\"}'`
Then interpret the result and continue with next tool if needed.