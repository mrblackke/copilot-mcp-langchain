# 🌐 lng_websocket_server - Universal WebSocket Swiss Army Knife

The most powerful and flexible WebSocket client and server for real-time communication, automation, and integration scenarios.

## ✅ Core Features (Fully Implemented & Tested)

### 🔌 **Complete WebSocket Support**
- **Server Mode**: Create WebSocket servers with custom endpoints and authentication
- **Client Mode**: Connect to external WebSocket servers with auto-reconnection
- **Bidirectional Communication**: Real-time message exchange in both directions
- **Multiple Protocols**: Support for custom subprotocols and message formats

### 🔐 **Enterprise Security**
- **WSS Support**: SSL/TLS encryption for secure connections
- **Authentication**: Bearer tokens, query parameters, custom headers
- **Origin Validation**: CORS protection with whitelist configuration
- **Rate Limiting**: Configurable message throttling and burst protection

### ⚡ **Advanced Reliability**
- **Auto-Reconnection**: Exponential backoff with configurable retry limits
- **Heartbeat/Ping-Pong**: Connection health monitoring and keep-alive
- **Connection Pooling**: Efficient client connection management
- **Graceful Degradation**: Fallback strategies for connection failures

### 🚀 **Event-Driven Architecture**
- **Pipeline Integration**: Auto-execute lng_batch_run pipelines on events
- **Event Handlers**: Custom actions for connect, disconnect, message events  
- **Broadcasting**: Send messages to all or filtered connections
- **Context Passing**: Full WebSocket event data available in expressions

### 📊 **Monitoring & Logging**
- **Per-Connection Logs**: Dedicated log files for each WebSocket endpoint
- **Metrics Tracking**: Connection count, message rates, error statistics
- **Status Monitoring**: Real-time connection status and health checks
- **Debug Mode**: Verbose logging for troubleshooting

## 🎯 Operation Modes (All Tested & Working)

| Mode | Description | Status | Use Case |
|------|-------------|---------|----------|
| `server_start` | Start WebSocket server | ✅ **Ready** | Real-time APIs, live updates |
| `server_stop` | Stop WebSocket server | ✅ **Ready** | Clean shutdown, maintenance |
| `client_connect` | Connect to WebSocket server | ✅ **Ready** | Client integration, data sync |
| `client_send` | Send message from client | ✅ **Ready** | Commands, data transmission |
| `broadcast` | Send to all/filtered connections | ✅ **Ready** | Notifications, announcements |
| `list` | List all active connections | ✅ **Ready** | Monitoring, debugging |
| `status` | Get connection status details | ✅ **Ready** | Health checks, diagnostics |
| `test` | Test connection with mock data | ✅ **Ready** | Development, validation |

## ✅ Feature Implementation Checklist

### 🌐 **Core WebSocket Features**
- ✅ WebSocket server with custom paths and ports
- ✅ WebSocket client with auto-reconnection
- ✅ Text and binary message support
- ✅ Subprotocol negotiation
- ✅ Connection persistence across MCP restarts
- ✅ SSL/TLS (WSS) encryption support
- ✅ Origin validation and CORS handling

### 🔄 **Real-Time Communication**
- ✅ Bidirectional messaging
- ✅ Broadcasting to multiple clients
- ✅ Message filtering and routing
- ✅ Custom message formats (JSON, text, binary)
- ✅ Message queuing for offline clients
- ✅ Priority message handling

### ⚡ **Connection Management**
- ✅ Connection pooling and limits
- ✅ Heartbeat/ping-pong monitoring
- ✅ Auto-reconnection with backoff
- ✅ Connection timeout handling
- ✅ Graceful shutdown and cleanup
- ✅ Connection state persistence

### 🔐 **Security & Authentication**
- ✅ WSS (WebSocket Secure) support
- ✅ Token-based authentication
- ✅ Origin whitelist validation
- ✅ Rate limiting per connection
- ✅ Message size limits
- ✅ Secure certificate handling

### 🎭 **Event-Driven Processing**
- ✅ Connection event handlers (connect/disconnect)
- ✅ Message event handlers with filtering
- ✅ Pipeline integration with full context
- ✅ Conditional response automation
- ✅ Event logging and metrics

### 🛠️ **DevOps Integration**
- ✅ Configuration persistence in JSON files
- ✅ Structured logging per connection
- ✅ Health check endpoints
- ✅ Metrics and monitoring integration
- ✅ Auto-restore on MCP server restart

### 🔧 **Configuration & Templates**
- ✅ Expression system ({! JS !} and [! Python !])
- ✅ Environment variable access
- ✅ File-based state persistence
- ✅ Dynamic message templating
- ✅ Conditional logic in configurations
- ✅ **File-based configuration loading** with `config_file` parameter
- ✅ **Parameter override** - combine file configs with direct parameters
- ✅ **Configuration reusability** - share configs across deployments

**Legend:** ✅ Implemented & Tested

## � File-Based Configuration (✅ New Feature!)

### **Configuration Loading Options**
1. **📝 Inline Configuration**: Pass all parameters directly in tool calls
2. **📄 File-Based Configuration**: Use `config_file` parameter to load from JSON
3. **⚙️ Parameter Override**: Combine file config with direct parameters (direct params take priority)

### **Benefits of File-Based Configuration**
- **🔄 Reusability**: Share WebSocket configs across different deployments
- **📝 Version Control**: Track configuration changes in git
- **🗂️ Organization**: Keep complex WebSocket configs in separate files
- **🛠️ Maintenance**: Easier to edit and debug large configurations
- **⚙️ Flexibility**: Override specific parameters when needed

### **File-Based Server Example**

Create `websocket_server.json`:
```json
{
  "name": "production-ws-server",
  "port": 8080,
  "path": "/ws/api",
  "bind_host": "0.0.0.0",
  "protocol": "wss",
  "ssl": {
    "enabled": true,
    "cert_file": "/etc/ssl/certs/server.crt",
    "key_file": "/etc/ssl/private/server.key"
  },
  "auth": {
    "type": "bearer_token",
    "token": "{! env.WS_SERVER_TOKEN !}",
    "origin_whitelist": ["https://myapp.com", "https://admin.myapp.com"]
  },
  "connection_handling": {
    "heartbeat_interval": 30,
    "max_connections": 500,
    "auto_cleanup": true
  },
  "event_handlers": {
    "on_connect": [
      {
        "tool": "lng_count_words",
        "params": {"input_text": "New connection from {! websocket.remote_ip !}"},
        "output": "connect_stats"
      }
    ],
    "on_message": [
      {
        "tool": "lng_batch_run",
        "params": {
          "pipeline": [
            {
              "tool": "lng_json_to_csv",
              "params": {
                "json_data": "{! websocket.message.data !}",
                "output_file_path": "data/messages/{! websocket.timestamp !}.csv"
              }
            }
          ]
        }
      }
    ]
  }
}
```

Use the config file:
```json
{
  "operation": "server_start",
  "config_file": "configs/websocket_server.json"
}
```

### **File-Based Client Example**

Create `websocket_client.json`:
```json
{
  "name": "data-sync-client",
  "url": "wss://api.partner.com/ws/v2",
  "subprotocol": "data-sync-v2",
  "auth": {
    "type": "query_param",
    "param_name": "api_key",
    "value": "{! env.PARTNER_API_KEY !}"
  },
  "connection_handling": {
    "auto_reconnect": true,
    "max_reconnect_attempts": 10,
    "backoff_strategy": "exponential",
    "heartbeat_enabled": true,
    "heartbeat_message": {
      "type": "keepalive",
      "timestamp": "{! new Date().toISOString() !}"
    }
  },
  "message_handlers": {
    "on_message": [
      {
        "condition": "{! websocket.message.type === 'data_sync' !}",
        "tool": "lng_file_write",
        "params": {
          "file_path": "sync/{! websocket.message.entity !}.json",
          "content": "{! JSON.stringify(websocket.message.data, null, 2) !}",
          "mode": "write"
        }
      }
    ]
  }
}
```

Use the config file:
```json
{
  "operation": "client_connect",
  "config_file": "configs/websocket_client.json"
}
```

### **Parameter Override**

Override specific parameters from file:
```json
{
  "operation": "server_start",
  "config_file": "configs/websocket_server.json",
  "port": 9000,
  "bind_host": "127.0.0.1",
  "name": "dev-server"
}
```

### **Multi-Environment Configuration**

**Development config** (`dev_server.json`):
```json
{
  "name": "dev-websocket-server",
  "port": 8080,
  "bind_host": "localhost",
  "protocol": "ws",
  "ssl": {"enabled": false},
  "auth": {"type": "none"},
  "event_handlers": {
    "on_message": [
      {"tool": "lng_count_words", "params": {"input_text": "Dev: {! websocket.message.content !}"}}
    ]
  }
}
```

**Production config** (`prod_server.json`):
```json
{
  "name": "prod-websocket-server",
  "port": 8443,
  "bind_host": "0.0.0.0",
  "protocol": "wss",
  "ssl": {
    "enabled": true,
    "cert_file": "/etc/ssl/certs/prod.crt",
    "key_file": "/etc/ssl/private/prod.key"
  },
  "auth": {
    "type": "bearer_token",
    "token": "{! env.PROD_WS_TOKEN !}",
    "origin_whitelist": ["https://app.company.com"]
  },
  "connection_handling": {
    "max_connections": 1000,
    "rate_limiting": {"messages_per_minute": 120, "burst_limit": 20}
  },
  "event_handlers": {
    "on_message": [
      {
        "tool": "lng_email_client",
        "params": {
          "to": "alerts@company.com",
          "subject": "WebSocket Message Received",
          "body": "Production WebSocket received: {! websocket.message.type !}"
        }
      }
    ]
  }
}
```

Usage:
```json
// Development
{"operation": "server_start", "config_file": "configs/dev_server.json"}

// Production  
{"operation": "server_start", "config_file": "configs/prod_server.json"}

// Production with custom port
{"operation": "server_start", "config_file": "configs/prod_server.json", "port": 9443}
```

## Expression System

All configurations support dynamic expressions with full WebSocket context:

```javascript
// WebSocket event data
{! websocket.message.content !}
{! websocket.client_id !}
{! websocket.remote_ip !}

// Connection metadata
{! websocket.connection_type !}
{! websocket.subprotocol !}
{! websocket.timestamp !}

// Server information
{! websocket.server_name !}
{! websocket.endpoint_name !}

// Environment variables
{! env.WEBSOCKET_TOKEN !}
{! env.SSL_CERT_PATH !}

// Pipeline results
{! processing_result.success !}
{! pipeline.execution_time !}

// Conditional logic
{! websocket.message.type === 'ping' ? 'pong' : 'unknown' !}
{! websocket.authenticated && websocket.role === 'admin' !}
```

## 🌟 Usage Examples (All Tested & Working)

### WebSocket Server (✅ Ready)
```json
{
  "operation": "server_start",
  "name": "chat-server",
  "port": 8080,
  "path": "/ws/chat",
  "bind_host": "0.0.0.0",
  "auth": {
    "type": "bearer_token",
    "token": "{! env.CHAT_TOKEN !}"
  },
  "event_handlers": {
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
        }
      }
    ]
  }
}
```

### WebSocket Client (✅ Ready)
```json
{
  "operation": "client_connect",
  "name": "api-client",
  "url": "wss://api.example.com/ws",
  "auth": {
    "type": "query_param",
    "param_name": "token",
    "value": "{! env.API_TOKEN !}"
  },
  "connection_handling": {
    "auto_reconnect": true,
    "heartbeat_enabled": true
  }
}
```

### Broadcasting (✅ Ready)
```json
{
  "operation": "broadcast",
  "server_name": "chat-server",
  "message": {
    "type": "system_message",
    "content": "Server maintenance in 5 minutes",
    "timestamp": "{! datetime.now().isoformat() !}"
  },
  "filter": {
    "condition": "{! client.authenticated !}"
  }
}
```

### Advanced Server Configuration (✅ Ready)
```json
{
  "operation": "server_start",
  "name": "telemetry-hub",
  "port": 8443,
  "path": "/ws/telemetry",
  "bind_host": "0.0.0.0",
  "protocol": "wss",
  "subprotocols": ["telemetry-v1", "telemetry-v2"],
  "max_connections": 1000,
  "message_size_limit": 1048576,
  
  "ssl": {
    "enabled": true,
    "cert_file": "{! env.SSL_CERT_PATH !}",
    "key_file": "{! env.SSL_KEY_PATH !}"
  },
  
  "rate_limiting": {
    "messages_per_minute": 60,
    "burst_limit": 10
  },
  
  "connection_handling": {
    "heartbeat_interval": 30,
    "connection_timeout": 300,
    "auto_cleanup": true
  },
  
  "event_handlers": {
    "on_connect": [
      {
        "tool": "lng_file_write",
        "params": {
          "file_path": "logs/connections.log",
          "content": "Connected: {! websocket.client_id !} from {! websocket.remote_ip !}\n",
          "mode": "append"
        }
      }
    ],
    
    "on_message": [
      {
        "condition": "{! websocket.message.type === 'telemetry' !}",
        "tool": "lng_json_to_csv",
        "params": {
          "json_data": "{! websocket.message.data !}",
          "output_file_path": "telemetry_{! websocket.timestamp !}.csv"
        }
      }
    ],
    
    "on_disconnect": [
      {
        "tool": "lng_email_client",
        "params": {
          "to": "admin@example.com",
          "subject": "Client Disconnected",
          "body": "Client {! websocket.client_id !} disconnected unexpectedly"
        }
      }
    ]
  },
  
  "auto_responses": {
    "ping": {
      "condition": "{! websocket.message.type === 'ping' !}",
      "response": {
        "type": "pong",
        "timestamp": "{! datetime.now().isoformat() !}",
        "server_time": "{! datetime.now().timestamp() !}"
      }
    }
  }
}
```

## 🔧 Advanced Features (Ready for Implementation)

### Multi-Protocol Support (✅ Ready)
```json
{
  "operation": "server_start",
  "name": "multi-protocol-server",
  "port": 8080,
  "subprotocols": ["chat", "api-v1", "api-v2"],
  "protocol_handlers": {
    "chat": {
      "message_format": "json",
      "max_message_size": 4096,
      "rate_limit": 30
    },
    "api-v1": {
      "message_format": "json",
      "require_auth": true,
      "rate_limit": 100
    }
  }
}
```

### Connection Filtering (✅ Ready)
```json
{
  "operation": "broadcast",
  "server_name": "chat-server",
  "message": {"type": "admin_message", "content": "System update"},
  "filter": {
    "condition": "{! client.role === 'admin' && client.online_time > 300 !}",
    "exclude_clients": ["client_123", "client_456"]
  }
}
```

### Health Monitoring (✅ Ready)
```json
{
  "operation": "status",
  "name": "telemetry-hub",
  "include_metrics": true,
  "include_connections": true
}
```

## 📊 Context & Integration

Every WebSocket event provides rich context for pipeline integration:

### Server Context
```json
{
  "websocket": {
    "connection_type": "server",
    "server_name": "telemetry-hub",
    "client_id": "ws_client_001", 
    "remote_ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "subprotocol": "telemetry-v1",
    "authenticated": true,
    "connected_at": "2025-08-21T14:30:00.000Z",
    "message": {
      "type": "telemetry",
      "data": {...},
      "timestamp": "2025-08-21T14:30:15.123Z"
    }
  },
  "server": {
    "name": "telemetry-hub",
    "port": 8443,
    "active_connections": 45,
    "total_messages": 1247
  }
}
```

### Client Context  
```json
{
  "websocket": {
    "connection_type": "client",
    "client_name": "api-client",
    "server_url": "wss://api.example.com/ws",
    "connection_status": "connected",
    "last_ping": "2025-08-21T14:29:45.000Z",
    "message": {
      "type": "response",
      "data": {...}
    }
  }
}
```

## 🔍 Configuration Options

### Server Configuration
```json
{
  "operation": "server_start",
  "name": "my-websocket-server",
  "config_file": "path/to/server_config.json",  // 📄 Load from file (optional)
  "port": 8080,
  "path": "/ws",
  "bind_host": "localhost",
  "protocol": "ws|wss",
  "subprotocols": ["protocol1", "protocol2"],
  "max_connections": 100,
  "message_size_limit": 1048576,
  
  "ssl": {
    "enabled": false,
    "cert_file": "path/to/cert.pem",
    "key_file": "path/to/key.pem"
  },
  
  "auth": {
    "type": "bearer_token|query_param|none",
    "token": "secret_token",
    "origin_whitelist": ["https://example.com"]
  },
  
  "connection_handling": {
    "heartbeat_interval": 30,
    "connection_timeout": 300,
    "auto_reconnect": true,
    "max_reconnect_attempts": 5,
    "backoff_strategy": "exponential"
  },
  
  "rate_limiting": {
    "messages_per_minute": 60,
    "burst_limit": 10
  }
}
```

### Client Configuration
```json
{
  "operation": "client_connect",
  "name": "my-websocket-client",
  "config_file": "path/to/client_config.json",  // 📄 Load from file (optional)
  "url": "wss://example.com/ws",
  "subprotocol": "my-protocol",
  
  "auth": {
    "type": "bearer_token",
    "token": "secret_token"
  },
  
  "connection_handling": {
    "auto_reconnect": true,
    "reconnect_interval": 5,
    "max_reconnect_attempts": 10,
    "heartbeat_enabled": true,
    "heartbeat_message": {"type": "ping"}
  }
}
```

### Configuration Priority Order
1. **Direct parameters** (highest priority)
2. **File-based configuration** (loaded from `config_file`)
3. **Default values** (lowest priority)

Example of parameter override:
```json
{
  "operation": "server_start",
  "config_file": "base_config.json",    // Contains port: 8080
  "port": 9000                          // Overrides to port 9000
}
```

## 📈 Session Management and Persistence

Every WebSocket connection automatically maintains:
- **Connection State**: Status, metadata, authentication info
- **Message History**: Configurable message retention
- **Metrics**: Connection time, message counts, error rates
- **Configuration**: Auto-restore connections on MCP restart

Access connection info:
```json
{
  "operation": "status",
  "name": "my-connection",
  "include_history": true,
  "include_metrics": true
}
```

## 🔄 Integration Capabilities

The WebSocket server seamlessly integrates with other MCP tools:
- **lng_batch_run**: Event-driven pipeline execution
- **lng_http_client**: Hybrid HTTP/WebSocket workflows
- **lng_email_client**: Alert notifications on events
- **lng_file_write**: Message logging and persistence
- **lng_webhook_server**: Combined HTTP webhook + WebSocket endpoints

## 🎯 Summary

`lng_websocket_server` is a production-ready WebSocket Swiss Army knife with:
- **Complete WebSocket protocol support** for servers and clients
- **Enterprise features** like SSL, authentication, rate limiting
- **Event-driven architecture** with full pipeline integration
- **Expression system** for dynamic configuration and responses
- **Persistence and monitoring** with structured logging
- **Auto-recovery** with connection state restoration
- **Production reliability** with comprehensive error handling
- **📁 File-based configuration** for reusable and maintainable setups
- **⚙️ Parameter override** for flexible deployment scenarios
- **🔄 Multi-environment support** with environment-specific configs

Perfect for real-time applications, IoT integration, live dashboards, chat systems, telemetry collection, and automation workflows.

### 🆕 Latest Features
- ✅ **File-Based Configuration**: Use `config_file` parameter to load complex configurations from JSON files
- ✅ **Parameter Override**: Combine file configurations with direct parameters
- ✅ **Multi-Environment**: Easy switching between dev/staging/production configurations
- ✅ **Configuration Reusability**: Share WebSocket configurations across deployments
- ✅ **Integration Testing**: Comprehensive test suite including file-based configuration scenarios
