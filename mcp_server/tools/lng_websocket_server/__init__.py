"""
Universal WebSocket Server and Client Tool

This tool provides comprehensive WebSocket functionality for real-time communication
with event-driven pipeline integration.

Features:
- WebSocket server and client support
- SSL/TLS encryption
- Authentication (Bearer, query params, headers)
- Auto-reconnection with backoff strategies
- Rate limiting and connection management
- Pipeline integration for event handling
- Persistent connection state management
- Broadcast messaging with filtering
- Comprehensive metrics and monitoring

The tool follows the same architectural patterns as lng_webhook_server for consistency
and integrates with the existing expression system and pipeline infrastructure.
"""

from .tool import tool_info, run_tool

__all__ = ['tool_info', 'run_tool']
