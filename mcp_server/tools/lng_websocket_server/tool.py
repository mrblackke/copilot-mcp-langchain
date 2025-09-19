import mcp.types as types
import json
import logging
import asyncio
import os
import mcp_server
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger('mcp_server.tools.lng_websocket_server')

# Global storage for active WebSocket connections
ACTIVE_CONNECTIONS: Dict[str, Dict] = {}

# Flag to track if connections have been restored
_connections_restored = False

async def tool_info() -> dict:
    return {
        "description": """Universal WebSocket server and client with event-driven pipeline integration.

**Universal WebSocket Constructor**
Create WebSocket servers and clients for real-time communication with automatic pipeline execution.

**Operations:**
• `server_start` - Create new WebSocket server endpoint
• `server_stop` - Stop WebSocket server by name
• `client_connect` - Connect to external WebSocket server
• `client_send` - Send message from client connection
• `client_disconnect` - Disconnect client connection
• `broadcast` - Send message to all/filtered server connections
• `list` - List all active connections
• `status` - Get detailed status of specific connection
• `test` - Test connection with mock data

**Features:**
**Bidirectional Communication** - Real-time server and client WebSocket support
**Enterprise Security** - WSS, authentication, origin validation, rate limiting
**Auto-Reconnection** - Heartbeat monitoring with exponential backoff retry
**Event-Driven** - Pipeline execution on connect/disconnect/message events
**Monitoring** - Structured logs, metrics, connection health tracking
**Persistence** - Auto-restore connections on MCP server restart
**File-Based Configuration** - Use `config_file` parameter to load WebSocket config from JSON files

**Configuration Loading:**
1. **Inline Configuration**: Pass all parameters directly in the tool call
2. **File-Based Configuration**: Use `config_file` parameter to load config from JSON file
3. **Parameter Override**: Can combine file config with direct parameters (direct params take priority)

**Example Server Configuration:**
```json
{
  "operation": "server_start",
  "name": "telemetry-server",
  "port": 8080,
  "path": "/ws/telemetry",
  "bind_host": "0.0.0.0",
  "protocol": "wss",
  "auth": {
    "type": "bearer_token",
    "token": "{! env.WEBSOCKET_TOKEN !}",
    "origin_whitelist": ["https://example.com"]
  },
  "ssl": {
    "enabled": true,
    "cert_file": "ssl/server.crt",
    "key_file": "ssl/server.key"
  },
  "connection_handling": {
    "heartbeat_interval": 30,
    "max_connections": 100,
    "auto_cleanup": true
  },
  "event_handlers": {
    "on_connect": [
      {
        "tool": "lng_file_write",
        "params": {
          "file_path": "logs/connections.log",
          "content": "Connected: {! websocket.client_id !} from {! websocket.remote_ip !}\\n",
          "mode": "append"
        }
      }
    ],
    "on_message": [
      {
        "tool": "lng_batch_run",
        "params": {
          "pipeline": [
            {
              "tool": "lng_count_words",
              "params": {"input_text": "{! websocket.message.content !}"},
              "output": "stats"
            }
          ]
        },
        "output": "processing_result"
      }
    ]
  }
}
```

**Example File-Based Server Configuration:**

Create a JSON file (e.g., `websocket_server.json`):
```json
{
  "name": "telemetry-server",
  "port": 8080,
  "path": "/ws/telemetry",
  "bind_host": "0.0.0.0",
  "protocol": "ws",
  "auth": {
    "type": "bearer_token",
    "token": "{! env.WEBSOCKET_TOKEN !}",
    "origin_whitelist": ["https://example.com"]
  },
  "connection_handling": {
    "heartbeat_interval": 30,
    "max_connections": 100,
    "auto_cleanup": true
  },
  "event_handlers": {
    "on_connect": [
      {
        "tool": "lng_file_write",
        "params": {
          "file_path": "logs/connections.log",
          "content": "Connected: {! websocket.client_id !} from {! websocket.remote_ip !}\\n",
          "mode": "append"
        }
      }
    ],
    "on_message": [
      {
        "tool": "lng_count_words",
        "params": {"input_text": "{! websocket.message.content !}"},
        "output": "stats"
      }
    ]
  }
}
```

Then use it:
```json
{
  "operation": "server_start",
  "config_file": "mcp_server/tools/lng_websocket_server/websocket_server.json"
}
```

**Example File-Based Client Configuration:**

Create a JSON file (e.g., `websocket_client.json`):
```json
{
  "name": "api-client",
  "url": "wss://api.example.com/ws",
  "subprotocol": "api-v1",
  "auth": {
    "type": "query_param",
    "param_name": "token",
    "value": "{! env.API_TOKEN !}"
  },
  "connection_handling": {
    "auto_reconnect": true,
    "heartbeat_enabled": true,
    "heartbeat_message": {"type": "ping"}
  },
  "message_handlers": {
    "on_message": [
      {
        "condition": "{! websocket.message.type === 'command' !}",
        "tool": "lng_websocket_server",
        "params": {
          "operation": "client_send",
          "name": "api-client", 
          "message": {
            "type": "response",
            "result": "Command executed",
            "timestamp": "{! datetime.now().isoformat() !}"
          }
        }
      }
    ]
  }
}
```

Then use it:
```json
{
  "operation": "client_connect",
  "config_file": "mcp_server/tools/lng_websocket_server/websocket_client.json"
}
```

**Parameter Merging:**
When using `config_file`, you can still override specific parameters:
```json
{
  "operation": "server_start",
  "config_file": "websocket_server.json",
  "port": 8081,
  "bind_host": "localhost"
}
```

**Benefits of File-Based Configuration:**
- **Reusability**: Share WebSocket configs across different deployments
- **Version Control**: Track WebSocket configuration changes in git
- **Organization**: Keep complex WebSocket configs in separate files  
- **Maintenance**: Easier to edit and debug large configurations
- **Parameter Override**: Can still override specific parameters when needed

**Example Client Configuration:**
```json
{
  "operation": "client_connect",
  "name": "api-client",
  "url": "wss://api.example.com/ws",
  "subprotocol": "api-v1",
  "auth": {
    "type": "query_param",
    "param_name": "token",
    "value": "{! env.API_TOKEN !}"
  },
  "connection_handling": {
    "auto_reconnect": true,
    "heartbeat_enabled": true,
    "heartbeat_message": {"type": "ping"}
  },
  "message_handlers": {
    "on_message": [
      {
        "condition": "{! websocket.message.type === 'command' !}",
        "tool": "lng_websocket_server",
        "params": {
          "operation": "client_send",
          "name": "api-client", 
          "message": {
            "type": "response",
            "result": "Command executed",
            "timestamp": "{! datetime.now().isoformat() !}"
          }
        }
      }
    ]
  }
}
```

**WebSocket Context Available in Pipeline:**
```json
{
  "websocket": {
    "timestamp": "2025-08-21T14:30:15.123Z",
    "connection_type": "server|client",
    "connection_name": "telemetry-server",
    "client_id": "ws_client_001",
    "remote_ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "subprotocol": "telemetry-v1",
    "authenticated": true,
    "connected_at": "2025-08-21T14:30:00.000Z",
    "message": {
      "type": "text|binary",
      "content": "Message content...",
      "size": 1024
    }
  },
  "connection": {
    "total_messages": 247,
    "connection_time": 1847.5,
    "last_activity": "2025-08-21T14:30:15.123Z"
  },
  "pipeline": {
    "execution_time": 0.156,
    "success": true,
    "error_id": null
  }
}
```""",
        "schema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Operation to perform",
                    "enum": ["server_start", "server_stop", "client_connect", "client_send", "client_disconnect", "broadcast", "list", "status", "test"]
                },
                "name": {
                    "type": "string",
                    "description": "Unique name for the WebSocket connection"
                },
                "port": {
                    "type": "integer",
                    "description": "Port number for WebSocket server (1000-65535)",
                    "minimum": 1000,
                    "maximum": 65535
                },
                "path": {
                    "type": "string",
                    "description": "URL path for WebSocket endpoint (e.g., '/ws/chat')"
                },
                "bind_host": {
                    "type": "string",
                    "description": "Host to bind server to ('localhost' or '0.0.0.0')"
                },
                "url": {
                    "type": "string",
                    "description": "WebSocket URL to connect to (for client operations)"
                },
                "protocol": {
                    "type": "string",
                    "description": "WebSocket protocol",
                    "enum": ["ws", "wss"],
                    "default": "ws"
                },
                "subprotocol": {
                    "type": "string",
                    "description": "WebSocket subprotocol"
                },
                "subprotocols": {
                    "type": "array",
                    "description": "Supported WebSocket subprotocols for servers",
                    "items": {"type": "string"}
                },
                "max_connections": {
                    "type": "integer",
                    "description": "Maximum concurrent connections for server",
                    "default": 100
                },
                "message_size_limit": {
                    "type": "integer",
                    "description": "Maximum message size in bytes",
                    "default": 1048576
                },
                "auth": {
                    "type": "object",
                    "description": "Authentication configuration",
                    "properties": {
                        "type": {"type": "string", "enum": ["bearer_token", "query_param", "header", "none"]},
                        "token": {"type": "string"},
                        "param_name": {"type": "string"},
                        "header_name": {"type": "string"},
                        "origin_whitelist": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "ssl": {
                    "type": "object",
                    "description": "SSL/TLS configuration",
                    "properties": {
                        "enabled": {"type": "boolean", "default": False},
                        "cert_file": {"type": "string"},
                        "key_file": {"type": "string"},
                        "ca_file": {"type": "string"}
                    }
                },
                "connection_handling": {
                    "type": "object",
                    "description": "Connection handling configuration",
                    "properties": {
                        "heartbeat_interval": {"type": "integer", "default": 30},
                        "connection_timeout": {"type": "integer", "default": 300},
                        "auto_reconnect": {"type": "boolean", "default": True},
                        "max_reconnect_attempts": {"type": "integer", "default": 5},
                        "backoff_strategy": {"type": "string", "enum": ["fixed", "exponential", "linear"], "default": "exponential"},
                        "heartbeat_enabled": {"type": "boolean", "default": True},
                        "heartbeat_message": {"type": "object"},
                        "auto_cleanup": {"type": "boolean", "default": True}
                    }
                },
                "rate_limiting": {
                    "type": "object",
                    "description": "Rate limiting configuration",
                    "properties": {
                        "messages_per_minute": {"type": "integer", "default": 60},
                        "burst_limit": {"type": "integer", "default": 10}
                    }
                },
                "event_handlers": {
                    "type": "object",
                    "description": "Event handlers for server connections",
                    "properties": {
                        "on_connect": {"type": "array", "items": {"type": "object"}},
                        "on_disconnect": {"type": "array", "items": {"type": "object"}},
                        "on_message": {"type": "array", "items": {"type": "object"}}
                    }
                },
                "message_handlers": {
                    "type": "object",
                    "description": "Message handlers for client connections",
                    "properties": {
                        "on_message": {"type": "array", "items": {"type": "object"}}
                    }
                },
                "auto_responses": {
                    "type": "object",
                    "description": "Automatic response configurations",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "condition": {"type": "string"},
                            "response": {"type": "object"}
                        }
                    }
                },
                "message": {
                    "description": "Message to send (for send/broadcast operations)"
                },
                "filter": {
                    "type": "object",
                    "description": "Filter configuration for broadcast operations",
                    "properties": {
                        "condition": {"type": "string"},
                        "include_clients": {"type": "array", "items": {"type": "string"}},
                        "exclude_clients": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "test_data": {
                    "type": "object",
                    "description": "Mock data for test operations"
                },
                "include_metrics": {
                    "type": "boolean",
                    "description": "Include metrics in status response",
                    "default": False
                },
                "include_connections": {
                    "type": "boolean", 
                    "description": "Include connection details in status response",
                    "default": False
                },
                "config_file": {
                    "type": "string",
                    "description": "Path to JSON file containing WebSocket configuration (alternative to inline config)"
                }
            },
            "required": ["operation"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Execute WebSocket operations."""
    
    global _connections_restored
    
    # Restore connections on first use if not done during init
    if not _connections_restored:
        await _ensure_connections_restored()
    
    try:
        operation = parameters.get("operation")
        
        if operation == "server_start":
            return await start_server(parameters)
        elif operation == "server_stop":
            return await stop_server(parameters)
        elif operation == "client_connect":
            return await connect_client(parameters)
        elif operation == "client_send":
            return await send_message(parameters)
        elif operation == "client_disconnect":
            return await disconnect_client(parameters)
        elif operation == "broadcast":
            return await broadcast_message(parameters)
        elif operation == "list":
            return await list_connections()
        elif operation == "status":
            return await connection_status(parameters)
        elif operation == "test":
            return await test_connection(parameters)
        else:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }, indent=2)
            )]
            
    except Exception as e:
        logger.error(f"Error in lng_websocket_server: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def start_server(params: dict) -> list[types.Content]:
    """Start a new WebSocket server."""
    try:
        # Store original params to detect config source
        original_params = params.copy()
        
        # Check if config_file is provided and load configuration
        if "config_file" in params:
            config_file = params["config_file"]
            logger.info(f"Loading WebSocket server configuration from file: {config_file}")
            
            try:
                # Read configuration from file
                if not os.path.isabs(config_file):
                    # Make relative paths relative to the project root
                    project_root = os.path.dirname(os.path.dirname(mcp_server.__file__))
                    config_file = os.path.join(project_root, config_file)
                
                logger.info(f"Resolved config file path: {config_file}")
                logger.info(f"File exists: {os.path.exists(config_file)}")
                
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                logger.info(f"Config loaded successfully, keys: {list(file_config.keys())}")
                
                # Merge file config with params, giving priority to direct params
                merged_params = file_config.copy()
                merged_params.update({k: v for k, v in params.items() if k != "config_file"})
                
                logger.info(f"Merged successfully, name param: {merged_params.get('name', 'NOT FOUND')}")
                logger.info(f"Successfully loaded WebSocket server configuration from {config_file}")
                params = merged_params
                
            except FileNotFoundError:
                return [types.TextContent(
                    type="text", 
                    text=json.dumps({
                        "success": False,
                        "error": f"Configuration file not found: {config_file}",
                        "config": {}
                    }, indent=2)
                )]
            except json.JSONDecodeError as e:
                return [types.TextContent(
                    type="text", 
                    text=json.dumps({
                        "success": False,
                        "error": f"Invalid JSON in configuration file {config_file}: {str(e)}",
                        "config": {}
                    }, indent=2)
                )]
        
        # Validate required parameters
        connection_name = params.get("name")
        port = params.get("port")
        path = params.get("path", "/ws")
        
        if not connection_name:
            raise ValueError("'name' parameter is required")
        if not port:
            raise ValueError("'port' parameter is required")
        
        # Validate port range
        if not (1000 <= port <= 65535):
            raise ValueError("Port must be between 1000 and 65535")
        
        # Stop existing connection with same name
        if connection_name in ACTIVE_CONNECTIONS:
            await _stop_connection_by_name(connection_name)
            logger.info(f"Stopped existing connection '{connection_name}' for restart")
        
        # Create server configuration
        config = {
            "name": connection_name,
            "type": "server",
            "port": port,
            "path": path,
            "bind_host": params.get("bind_host", "localhost"),
            "protocol": params.get("protocol", "ws"),
            "subprotocols": params.get("subprotocols", []),
            "max_connections": params.get("max_connections", 100),
            "message_size_limit": params.get("message_size_limit", 1048576),
            "auth": params.get("auth", {"type": "none"}),
            "ssl": params.get("ssl", {"enabled": False}),
            "connection_handling": params.get("connection_handling", {
                "heartbeat_interval": 30,
                "connection_timeout": 300,
                "auto_cleanup": True
            }),
            "rate_limiting": params.get("rate_limiting", {
                "messages_per_minute": 60,
                "burst_limit": 10
            }),
            "event_handlers": params.get("event_handlers", {}),
            "auto_responses": params.get("auto_responses", {}),
            "created_at": datetime.now().isoformat(),
            "status": "starting",
            "clients": {},
            "metrics": {
                "total_connections": 0,
                "active_connections": 0,
                "total_messages": 0,
                "started_at": datetime.now().isoformat()
            }
        }
        
        # Save configuration to file
        await _save_connection_config(connection_name, config)
        
        # Start WebSocket server
        server_info = await _start_websocket_server(config)
        
        # Update status and store server info
        config["status"] = "running"
        config["server_info"] = server_info
        
        # Store in memory
        ACTIVE_CONNECTIONS[connection_name] = config
        
        # Save updated config
        await _save_connection_config(connection_name, config)
        
        protocol = "wss" if config["ssl"]["enabled"] else "ws"
        endpoint_url = f"{protocol}://{config['bind_host']}:{port}{path}"
        
        logger.info(f"WebSocket server '{connection_name}' started on {endpoint_url}")
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "message": f"WebSocket server '{connection_name}' started successfully",
                "connection_type": "server",
                "endpoint": endpoint_url,
                "config": _mask_sensitive_data(config),
                "config_source": "config_file" if "config_file" in original_params else "inline"
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def stop_server(params: dict) -> list[types.Content]:
    """Stop a WebSocket server."""
    try:
        connection_name = params.get("name")
        if not connection_name:
            raise ValueError("'name' parameter is required")
        
        if connection_name not in ACTIVE_CONNECTIONS:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"WebSocket connection '{connection_name}' not found"
                }, indent=2)
            )]
        
        config = ACTIVE_CONNECTIONS[connection_name]
        if config.get("type") != "server":
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Connection '{connection_name}' is not a server"
                }, indent=2)
            )]
        
        await _stop_connection_by_name(connection_name)
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "message": f"WebSocket server '{connection_name}' stopped successfully"
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to stop WebSocket server: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def connect_client(params: dict) -> list[types.Content]:
    """Connect to a WebSocket server as client."""
    try:
        # Store original params to detect config source
        original_params = params.copy()
        
        # Check if config_file is provided and load configuration
        if "config_file" in params:
            config_file = params["config_file"]
            logger.info(f"Loading WebSocket client configuration from file: {config_file}")
            
            try:
                # Read configuration from file
                if not os.path.isabs(config_file):
                    # Make relative paths relative to the project root
                    project_root = os.path.dirname(os.path.dirname(mcp_server.__file__))
                    config_file = os.path.join(project_root, config_file)
                
                logger.info(f"Resolved config file path: {config_file}")
                logger.info(f"File exists: {os.path.exists(config_file)}")
                
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                logger.info(f"Config loaded successfully, keys: {list(file_config.keys())}")
                
                # Merge file config with params, giving priority to direct params
                merged_params = file_config.copy()
                merged_params.update({k: v for k, v in params.items() if k != "config_file"})
                
                logger.info(f"Merged successfully, name param: {merged_params.get('name', 'NOT FOUND')}")
                logger.info(f"Successfully loaded WebSocket client configuration from {config_file}")
                params = merged_params
                
            except FileNotFoundError:
                return [types.TextContent(
                    type="text", 
                    text=json.dumps({
                        "success": False,
                        "error": f"Configuration file not found: {config_file}",
                        "config": {}
                    }, indent=2)
                )]
            except json.JSONDecodeError as e:
                return [types.TextContent(
                    type="text", 
                    text=json.dumps({
                        "success": False,
                        "error": f"Invalid JSON in configuration file {config_file}: {str(e)}",
                        "config": {}
                    }, indent=2)
                )]
        
        # Validate required parameters
        connection_name = params.get("name")
        url = params.get("url")
        
        if not connection_name:
            raise ValueError("'name' parameter is required")
        if not url:
            raise ValueError("'url' parameter is required")
        
        # Stop existing connection with same name
        if connection_name in ACTIVE_CONNECTIONS:
            await _stop_connection_by_name(connection_name)
            logger.info(f"Stopped existing connection '{connection_name}' for restart")
        
        # Create client configuration
        config = {
            "name": connection_name,
            "type": "client",
            "url": url,
            "subprotocol": params.get("subprotocol"),
            "auth": params.get("auth", {"type": "none"}),
            "connection_handling": params.get("connection_handling", {
                "auto_reconnect": True,
                "max_reconnect_attempts": 5,
                "backoff_strategy": "exponential",
                "heartbeat_enabled": True,
                "heartbeat_message": {"type": "ping"}
            }),
            "message_handlers": params.get("message_handlers", {}),
            "created_at": datetime.now().isoformat(),
            "status": "connecting",
            "metrics": {
                "connection_attempts": 0,
                "total_messages_sent": 0,
                "total_messages_received": 0,
                "last_activity": None
            }
        }
        
        # Save configuration to file
        await _save_connection_config(connection_name, config)
        
        # Start WebSocket client
        client_info = await _start_websocket_client(config)
        
        # Update status and store client info
        config["status"] = "connected" if client_info["connected"] else "failed"
        config["client_info"] = client_info
        
        # Store in memory
        ACTIVE_CONNECTIONS[connection_name] = config
        
        # Save updated config
        await _save_connection_config(connection_name, config)
        
        logger.info(f"WebSocket client '{connection_name}' connected to {url}")
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": client_info["connected"],
                "message": f"WebSocket client '{connection_name}' {'connected' if client_info['connected'] else 'failed to connect'}",
                "connection_type": "client",
                "url": url,
                "config": _mask_sensitive_data(config),
                "config_source": "config_file" if "config_file" in original_params else "inline"
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to connect WebSocket client: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def send_message(params: dict) -> list[types.Content]:
    """Send message from client connection."""
    try:
        connection_name = params.get("name")
        message = params.get("message")
        
        if not connection_name:
            raise ValueError("'name' parameter is required")
        if message is None:
            raise ValueError("'message' parameter is required")
        
        if connection_name not in ACTIVE_CONNECTIONS:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"WebSocket connection '{connection_name}' not found"
                }, indent=2)
            )]
        
        config = ACTIVE_CONNECTIONS[connection_name]
        if config.get("type") != "client":
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Connection '{connection_name}' is not a client"
                }, indent=2)
            )]
        
        # Send message using client instance
        result = await _send_client_message(connection_name, message)
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": result["success"],
                "message": f"Message {'sent' if result['success'] else 'failed to send'}",
                "connection_name": connection_name,
                "message_content": message,
                "error": result.get("error")
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def disconnect_client(params: dict) -> list[types.Content]:
    """Disconnect client connection."""
    try:
        connection_name = params.get("name")
        if not connection_name:
            raise ValueError("'name' parameter is required")
        
        if connection_name not in ACTIVE_CONNECTIONS:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"WebSocket connection '{connection_name}' not found"
                }, indent=2)
            )]
        
        config = ACTIVE_CONNECTIONS[connection_name]
        if config.get("type") != "client":
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Connection '{connection_name}' is not a client"
                }, indent=2)
            )]
        
        await _stop_connection_by_name(connection_name)
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "message": f"WebSocket client '{connection_name}' disconnected successfully"
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to disconnect client: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def broadcast_message(params: dict) -> list[types.Content]:
    """Broadcast message to server connections."""
    try:
        server_name = params.get("name")
        message = params.get("message")
        filter_config = params.get("filter", {})
        
        if not server_name:
            raise ValueError("'name' parameter is required for broadcast")
        if message is None:
            raise ValueError("'message' parameter is required")
        
        if server_name not in ACTIVE_CONNECTIONS:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"WebSocket server '{server_name}' not found"
                }, indent=2)
            )]
        
        config = ACTIVE_CONNECTIONS[server_name]
        if config.get("type") != "server":
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Connection '{server_name}' is not a server"
                }, indent=2)
            )]
        
        # Broadcast message to clients
        result = await _broadcast_to_clients(server_name, message, filter_config)
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "message": f"Message broadcasted to {result['sent_count']} clients",
                "server_name": server_name,
                "sent_count": result["sent_count"],
                "failed_count": result["failed_count"],
                "total_clients": result["total_clients"]
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to broadcast message: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def list_connections() -> list[types.Content]:
    """List all active WebSocket connections."""
    try:
        connections_summary = {}
        
        for name, config in ACTIVE_CONNECTIONS.items():
            summary = {
                "name": name,
                "type": config.get("type"),
                "status": config.get("status"),
                "created_at": config.get("created_at")
            }
            
            if config.get("type") == "server":
                summary.update({
                    "port": config.get("port"),
                    "path": config.get("path"),
                    "active_clients": len(config.get("clients", {})),
                    "total_connections": config.get("metrics", {}).get("total_connections", 0)
                })
            elif config.get("type") == "client":
                summary.update({
                    "url": config.get("url"),
                    "last_activity": config.get("metrics", {}).get("last_activity")
                })
            
            connections_summary[name] = summary
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "total_connections": len(ACTIVE_CONNECTIONS),
                "connections": connections_summary
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to list connections: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def connection_status(params: dict) -> list[types.Content]:
    """Get detailed status of specific connection."""
    try:
        connection_name = params.get("name")
        include_metrics = params.get("include_metrics", False)
        include_connections = params.get("include_connections", False)
        
        if not connection_name:
            raise ValueError("'name' parameter is required")
        
        if connection_name not in ACTIVE_CONNECTIONS:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"WebSocket connection '{connection_name}' not found"
                }, indent=2)
            )]
        
        config = ACTIVE_CONNECTIONS[connection_name]
        status_data = {
            "name": connection_name,
            "type": config.get("type"),
            "status": config.get("status"),
            "created_at": config.get("created_at")
        }
        
        if include_metrics and "metrics" in config:
            status_data["metrics"] = config["metrics"]
        
        if include_connections and config.get("type") == "server":
            status_data["clients"] = config.get("clients", {})
        
        # Add type-specific information
        if config.get("type") == "server":
            status_data.update({
                "endpoint": f"{'wss' if config.get('ssl', {}).get('enabled') else 'ws'}://{config.get('bind_host')}:{config.get('port')}{config.get('path')}",
                "active_clients": len(config.get("clients", {}))
            })
        elif config.get("type") == "client":
            status_data.update({
                "url": config.get("url"),
                "connection_attempts": config.get("metrics", {}).get("connection_attempts", 0)
            })
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "connection_status": status_data
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to get connection status: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def test_connection(params: dict) -> list[types.Content]:
    """Test WebSocket connection with mock data."""
    try:
        connection_name = params.get("name")
        test_data = params.get("test_data", {"type": "test", "message": "Hello WebSocket!"})
        
        if not connection_name:
            raise ValueError("'name' parameter is required")
        
        if connection_name not in ACTIVE_CONNECTIONS:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"WebSocket connection '{connection_name}' not found"
                }, indent=2)
            )]
        
        config = ACTIVE_CONNECTIONS[connection_name]
        
        # Test based on connection type
        if config.get("type") == "server":
            # For server, test by broadcasting test message
            result = await _broadcast_to_clients(connection_name, test_data, {})
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"Test message sent to {result['sent_count']} clients",
                    "connection_name": connection_name,
                    "test_data": test_data,
                    "sent_count": result["sent_count"],
                    "failed_count": result["failed_count"]
                }, indent=2)
            )]
            
        elif config.get("type") == "client":
            # For client, test by sending test message
            result = await _send_client_message(connection_name, test_data)
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": result["success"],
                    "message": f"Test message {'sent' if result['success'] else 'failed'}",
                    "connection_name": connection_name,
                    "test_data": test_data,
                    "error": result.get("error")
                }, indent=2)
            )]
        
        else:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Unknown connection type: {config.get('type')}"
                }, indent=2)
            )]
        
    except Exception as e:
        logger.error(f"Failed to test connection: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

# Helper functions

async def _save_connection_config(name: str, config: dict):
    """Save WebSocket connection configuration to file."""
    config_dir = "mcp_server/config/websocket"
    os.makedirs(config_dir, exist_ok=True)
    
    # Create a clean config copy without instances
    clean_config = {k: v for k, v in config.items() if not k.startswith('_')}
    
    config_file = os.path.join(config_dir, f"{name}.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(clean_config, f, indent=2, ensure_ascii=False)

async def _start_websocket_server(config: dict) -> dict:
    """Start WebSocket server."""
    try:
        from .websocket_server import WebSocketServerManager
        
        # Create and start WebSocket server
        server = WebSocketServerManager(config)
        server_info = await server.start()
        
        # Store server instance for later cleanup
        config['_server_instance'] = server
        
        return server_info
        
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {e}")
        raise

async def _start_websocket_client(config: dict) -> dict:
    """Start WebSocket client."""
    try:
        from .websocket_client import WebSocketClientManager
        
        # Create and start WebSocket client
        client = WebSocketClientManager(config)
        client_info = await client.connect()
        
        # Store client instance for later cleanup
        config['_client_instance'] = client
        
        return client_info
        
    except Exception as e:
        logger.error(f"Failed to start WebSocket client: {e}")
        return {"connected": False, "error": str(e)}

async def _send_client_message(connection_name: str, message: Any) -> dict:
    """Send message from client connection."""
    try:
        config = ACTIVE_CONNECTIONS.get(connection_name)
        if not config or not config.get('_client_instance'):
            return {"success": False, "error": "Client instance not found"}
        
        client = config['_client_instance']
        result = await client.send_message(message)
        
        # Update metrics
        if "metrics" in config:
            config["metrics"]["total_messages_sent"] += 1
            config["metrics"]["last_activity"] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

async def _broadcast_to_clients(server_name: str, message: Any, filter_config: dict) -> dict:
    """Broadcast message to server clients."""
    try:
        config = ACTIVE_CONNECTIONS.get(server_name)
        if not config or not config.get('_server_instance'):
            return {"sent_count": 0, "failed_count": 0, "total_clients": 0}
        
        server = config['_server_instance']
        result = await server.broadcast_message(message, filter_config)
        
        # Update metrics
        if "metrics" in config:
            config["metrics"]["total_messages"] += result["sent_count"]
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to broadcast message: {e}")
        return {"sent_count": 0, "failed_count": 1, "total_clients": 0}

async def _stop_connection_by_name(name: str):
    """Stop WebSocket connection by name."""
    if name in ACTIVE_CONNECTIONS:
        config = ACTIVE_CONNECTIONS[name]
        
        # Stop server or client instance
        if config.get("type") == "server" and config.get('_server_instance'):
            try:
                await config['_server_instance'].stop()
            except Exception as e:
                logger.error(f"Error stopping WebSocket server '{name}': {e}")
        elif config.get("type") == "client" and config.get('_client_instance'):
            try:
                await config['_client_instance'].disconnect()
            except Exception as e:
                logger.error(f"Error stopping WebSocket client '{name}': {e}")
        
        # Remove from active connections
        del ACTIVE_CONNECTIONS[name]
        
        # Remove config file
        config_file = f"mcp_server/config/websocket/{name}.json"
        if os.path.exists(config_file):
            os.remove(config_file)
            
        logger.info(f"WebSocket connection '{name}' stopped and cleaned up")

def _mask_sensitive_data(config: dict) -> dict:
    """Mask sensitive data in configuration."""
    masked = config.copy()
    
    # Remove instances from output
    for key in list(masked.keys()):
        if key.startswith('_'):
            del masked[key]
    
    # Mask auth secrets
    if "auth" in masked and "token" in masked["auth"]:
        token = masked["auth"]["token"]
        if len(token) > 6:
            masked["auth"]["token"] = token[:3] + "***" + token[-3:]
        else:
            masked["auth"]["token"] = "***"
    
    # Mask SSL key paths
    if "ssl" in masked and "key_file" in masked["ssl"]:
        masked["ssl"]["key_file"] = "***masked***"
    
    return masked

# Auto-restore connections on module import
def init():
    """Initialize WebSocket server - restore connections from saved configurations."""
    logger.info("Initializing WebSocket server - restoring saved configurations")
    
    try:
        config_dir = "mcp_server/config/websocket"
        if not os.path.exists(config_dir):
            logger.info("No websocket directory found, skipping restoration")
            return
        
        config_files = [f for f in os.listdir(config_dir) if f.endswith('.json')]
        if not config_files:
            logger.info("No WebSocket configurations found to restore")
            return
        
        logger.info(f"Found {len(config_files)} WebSocket configurations to restore")
        
        # Schedule restoration for when event loop is available
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_restore_connections_async())
            logger.info("WebSocket restoration scheduled in existing event loop")
        except RuntimeError:
            logger.info("No event loop available at init, connections will restore on first use")
        
    except Exception as e:
        logger.error(f"Error in WebSocket init: {e}")

async def _ensure_connections_restored():
    """Ensure connections are restored - called on first tool use if not restored during init."""
    global _connections_restored
    
    if _connections_restored:
        return
    
    try:
        await _restore_connections_async()
        _connections_restored = True
    except Exception as e:
        logger.error(f"Failed to restore WebSocket connections: {e}")

async def _restore_connections_async():
    """Restore WebSocket connections from configuration files."""
    try:
        config_dir = "mcp_server/config/websocket"
        if not os.path.exists(config_dir):
            return
        
        config_files = [f for f in os.listdir(config_dir) if f.endswith('.json')]
        
        for config_file in config_files:
            try:
                connection_name = config_file[:-5]  # Remove .json extension
                
                with open(os.path.join(config_dir, config_file), 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                logger.info(f"Restoring WebSocket connection '{connection_name}'")
                
                # Update status to indicate restoration
                config["status"] = "restoring"
                
                # Restore based on connection type
                if config.get("type") == "server":
                    server_info = await _start_websocket_server(config)
                    config["status"] = "running"
                    config["server_info"] = server_info
                elif config.get("type") == "client":
                    client_info = await _start_websocket_client(config)
                    config["status"] = "connected" if client_info.get("connected") else "failed"
                    config["client_info"] = client_info
                
                # Store in memory
                ACTIVE_CONNECTIONS[connection_name] = config
                
                logger.info(f"WebSocket connection '{connection_name}' restored successfully")
                
            except Exception as e:
                logger.error(f"Failed to restore WebSocket connection from {config_file}: {e}")
        
        logger.info(f"Restored {len(ACTIVE_CONNECTIONS)} WebSocket connections")
        
    except Exception as e:
        logger.error(f"Error during WebSocket connections restoration: {e}")

# Initialize when module is imported
init()
