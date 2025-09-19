"""
Cookie Grabber Tool for Managing WebSocket/Webhook Servers

This tool provides comprehensive cookie grabbing functionality with server management:
- Start/stop/restart webhook and websocket servers
- Process cookie data from Chrome extension
- Save cookies to organized file structure

Operations:
- start: Start webhook and websocket servers
- stop: Stop webhook and websocket servers  
- restart: Stop then start servers
- process: Process cookie data and save to files

The tool integrates directly with lng_webhook_server and lng_websocket_server
for deterministic server management without MCP calls.
"""

from .tool import tool_info, run_tool

__all__ = ['tool_info', 'run_tool']
