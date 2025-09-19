"""
Examples for lng_websocket_server tool usage.

This file contains practical examples demonstrating various WebSocket scenarios
and configurations for real-world applications.
"""

# Example 1: Simple WebSocket Server
SIMPLE_SERVER_EXAMPLE = {
    "operation": "server_start",
    "name": "chat-server",
    "port": 8080,
    "path": "/ws/chat",
    "bind_host": "0.0.0.0",
    "event_handlers": {
        "on_connect": [
            {
                "tool": "lng_file_write",
                "params": {
                    "file_path": "logs/chat_connections.log",
                    "content": "[{! datetime.now().isoformat() !}] User connected: {! websocket.client_id !} from {! websocket.remote_ip !}\n",
                    "mode": "append"
                }
            }
        ],
        "on_message": [
            {
                "tool": "lng_websocket_server",
                "params": {
                    "operation": "broadcast",
                    "name": "chat-server",
                    "message": {
                        "type": "chat_message",
                        "from": "{! websocket.client_id !}",
                        "message": "{! websocket.message.content !}",
                        "timestamp": "{! datetime.now().isoformat() !}"
                    },
                    "filter": {
                        "exclude_clients": ["{! websocket.client_id !}"]
                    }
                }
            }
        ]
    }
}

# Example 2: Secure WebSocket Server with Authentication
SECURE_SERVER_EXAMPLE = {
    "operation": "server_start",
    "name": "secure-api-server",
    "port": 8443,
    "path": "/ws/api",
    "protocol": "wss",
    "auth": {
        "type": "bearer_token",
        "token": "{! env.WEBSOCKET_API_TOKEN !}",
        "origin_whitelist": ["https://example.com", "https://app.example.com"]
    },
    "ssl": {
        "enabled": True,
        "cert_file": "ssl/server.crt",
        "key_file": "ssl/server.key"
    },
    "connection_handling": {
        "heartbeat_interval": 30,
        "max_connections": 100,
        "auto_cleanup": True,
        "connection_timeout": 300
    },
    "rate_limiting": {
        "messages_per_minute": 60,
        "burst_limit": 10
    },
    "event_handlers": {
        "on_connect": [
            {
                "tool": "lng_http_client",
                "params": {
                    "mode": "request",
                    "url": "https://api.example.com/websocket/connect",
                    "method": "POST",
                    "headers": {"Authorization": "Bearer {! env.API_TOKEN !}"},
                    "json": {
                        "client_id": "{! websocket.client_id !}",
                        "ip": "{! websocket.remote_ip !}",
                        "user_agent": "{! websocket.user_agent !}",
                        "timestamp": "{! websocket.timestamp !}"
                    }
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
                            "output": "word_stats"
                        },
                        {
                            "tool": "lng_file_write",
                            "params": {
                                "file_path": "data/message_log_{! datetime.now().strftime('%Y-%m-%d') !}.jsonl",
                                "content": "{! JSON.stringify({'client': websocket.client_id, 'message': websocket.message, 'stats': word_stats, 'timestamp': websocket.timestamp}) !}\n",
                                "mode": "append"
                            }
                        }
                    ]
                }
            }
        ]
    }
}

# Example 3: WebSocket Client with Auto-Reconnection
CLIENT_EXAMPLE = {
    "operation": "client_connect",
    "name": "api-monitor",
    "url": "wss://api.example.com/ws/monitor",
    "subprotocol": "monitor-v1",
    "auth": {
        "type": "query_param",
        "param_name": "token",
        "value": "{! env.MONITOR_TOKEN !}"
    },
    "connection_handling": {
        "auto_reconnect": True,
        "max_reconnect_attempts": 10,
        "backoff_strategy": "exponential",
        "heartbeat_enabled": True,
        "heartbeat_message": {
            "type": "ping",
            "timestamp": "{! datetime.now().isoformat() !}"
        }
    },
    "message_handlers": {
        "on_message": [
            {
                "condition": "{! websocket.message.type === 'alert' !}",
                "tool": "lng_email_client",
                "params": {
                    "mode": "send",
                    "service": "smtp",
                    "smtp_config": {
                        "host": "smtp.gmail.com",
                        "port": 587,
                        "username": "{! env.GMAIL_USER !}",
                        "password": "{! env.GMAIL_APP_PASSWORD !}",
                        "use_tls": True
                    },
                    "from_email": "monitor@example.com",
                    "to": "admin@example.com",
                    "subject": "WebSocket Alert: {! websocket.message.title !}",
                    "body_text": "Alert received from WebSocket: {! websocket.message.description !}\n\nTimestamp: {! websocket.timestamp !}\nSeverity: {! websocket.message.severity !}"
                }
            },
            {
                "condition": "{! websocket.message.type === 'data' !}",
                "tool": "lng_file_write",
                "params": {
                    "file_path": "data/monitor_data.jsonl",
                    "content": "{! JSON.stringify(websocket.message) !}\n",
                    "mode": "append"
                }
            }
        ]
    }
}

# Example 4: GitHub Copilot Telemetry Processing
TELEMETRY_SERVER_EXAMPLE = {
    "operation": "server_start",
    "name": "copilot-telemetry",
    "port": 8090,
    "path": "/ws/telemetry",
    "bind_host": "localhost",
    "max_connections": 50,
    "event_handlers": {
        "on_connect": [
            {
                "tool": "lng_count_words",
                "params": {"input_text": "New telemetry connection established"},
                "output": "connection_log"
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
                                "json_data": "{! [websocket.message] !}",
                                "format": "csv"
                            },
                            "output": "csv_data"
                        },
                        {
                            "tool": "lng_file_write",
                            "params": {
                                "file_path": "work/telemetry/daily_data_{! datetime.now().strftime('%Y-%m-%d') !}.csv",
                                "content": "{! csv_data !}",
                                "mode": "append"
                            }
                        }
                    ]
                }
            }
        ]
    }
}

# Example 5: Broadcast with Filtering
BROADCAST_EXAMPLE = {
    "operation": "broadcast",
    "name": "notification-server",
    "message": {
        "type": "system_notification",
        "title": "Server Maintenance",
        "body": "Scheduled maintenance will begin in 5 minutes",
        "priority": "high",
        "timestamp": "{! datetime.now().isoformat() !}"
    },
    "filter": {
        "condition": "{! client.authenticated === true && client.message_count > 0 !}",
        "exclude_clients": ["admin_client_001"]
    }
}

# Example 6: Auto-Response Configuration
AUTO_RESPONSE_SERVER_EXAMPLE = {
    "operation": "server_start",
    "name": "support-bot",
    "port": 8085,
    "path": "/ws/support",
    "auto_responses": {
        "help_request": {
            "condition": "{! websocket.message.type === 'help' || websocket.message.content.toLowerCase().includes('help') !}",
            "response": {
                "type": "bot_response",
                "message": "Hello! How can I assist you today? Available commands: /status, /info, /contact",
                "timestamp": "{! datetime.now().isoformat() !}",
                "bot_id": "support-bot-v1"
            }
        },
        "status_check": {
            "condition": "{! websocket.message.content === '/status' !}",
            "response": {
                "type": "status_response",
                "status": "online",
                "uptime": "{! Math.floor((Date.now() - new Date('{! datetime.now().isoformat() !}').getTime()) / 1000) !} seconds",
                "active_connections": "{! Object.keys(clients || {}).length !}"
            }
        }
    },
    "event_handlers": {
        "on_message": [
            {
                "condition": "{! websocket.message.content.startsWith('/contact') !}",
                "tool": "lng_email_client",
                "params": {
                    "mode": "send",
                    "service": "smtp",
                    "smtp_config": {
                        "host": "{! env.SMTP_HOST !}",
                        "username": "{! env.SMTP_USER !}",
                        "password": "{! env.SMTP_PASSWORD !}"
                    },
                    "from_email": "support-bot@example.com",
                    "to": "support-team@example.com",
                    "subject": "WebSocket Support Request",
                    "body_text": "Support request from WebSocket client {! websocket.client_id !}:\n\n{! websocket.message.content !}\n\nClient IP: {! websocket.remote_ip !}\nTimestamp: {! websocket.timestamp !}"
                }
            }
        ]
    }
}

# Example 7: Multi-Protocol Client Connection
MULTI_PROTOCOL_CLIENT = {
    "operation": "client_connect",
    "name": "multi-service-client",
    "url": "ws://localhost:8080/ws/multi",
    "subprotocol": "json-rpc-2.0",
    "connection_handling": {
        "auto_reconnect": True,
        "heartbeat_enabled": True,
        "heartbeat_message": {
            "jsonrpc": "2.0",
            "method": "ping",
            "id": "{! Date.now() !}"
        }
    },
    "message_handlers": {
        "on_message": [
            {
                "condition": "{! websocket.message.jsonrpc && websocket.message.method !}",
                "tool": "lng_javascript_execute",
                "params": {
                    "function_name": "processJsonRpcMessage",
                    "parameters": {
                        "message": "{! websocket.message !}",
                        "client_name": "{! websocket.connection_name !}"
                    }
                }
            }
        ]
    }
}

# Example 8: Load Testing Configuration
LOAD_TEST_CLIENT = {
    "operation": "client_connect",
    "name": "load-test-client-{! env.CLIENT_ID || '001' !}",
    "url": "ws://localhost:8080/ws/test",
    "connection_handling": {
        "auto_reconnect": False,
        "heartbeat_enabled": False
    },
    "message_handlers": {
        "on_message": [
            {
                "tool": "lng_math_calculator",
                "params": {"expression": "{! websocket.message.test_data.a !} + {! websocket.message.test_data.b !}"},
                "output": "calculation_result"
            },
            {
                "tool": "lng_websocket_server",
                "params": {
                    "operation": "client_send",
                    "name": "load-test-client-{! env.CLIENT_ID || '001' !}",
                    "message": {
                        "type": "test_response",
                        "result": "{! calculation_result !}",
                        "timestamp": "{! datetime.now().isoformat() !}"
                    }
                }
            }
        ]
    }
}

# All examples collection
EXAMPLES = {
    "simple_server": SIMPLE_SERVER_EXAMPLE,
    "secure_server": SECURE_SERVER_EXAMPLE,
    "client_with_reconnection": CLIENT_EXAMPLE,
    "telemetry_server": TELEMETRY_SERVER_EXAMPLE,
    "broadcast_with_filter": BROADCAST_EXAMPLE,
    "auto_response_server": AUTO_RESPONSE_SERVER_EXAMPLE,
    "multi_protocol_client": MULTI_PROTOCOL_CLIENT,
    "load_test_client": LOAD_TEST_CLIENT
}

def get_example(name: str) -> dict:
    """Get example configuration by name."""
    return EXAMPLES.get(name, {})

def list_examples() -> list:
    """List all available example names."""
    return list(EXAMPLES.keys())
