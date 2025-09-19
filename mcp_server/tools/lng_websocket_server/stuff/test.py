import unittest
import json
import asyncio
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock, AsyncMock

# Add parent directory to path to import tool module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tool import run_tool, ACTIVE_CONNECTIONS


class TestWebSocketServer(unittest.TestCase):
    """Test cases for lng_websocket_server tool using approval testing approach."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Clear active connections
        ACTIVE_CONNECTIONS.clear()
        
        # Create temporary directory for test configs
        self.test_config_dir = tempfile.mkdtemp()
        self.original_config_dir = "mcp_server/config/websocket"
        
        # Patch config directory
        self.config_patch = patch('tool._save_connection_config', new_callable=AsyncMock)
        self.mock_save_config = self.config_patch.start()

    def tearDown(self):
        """Clean up after each test."""
        # Stop all patches
        self.config_patch.stop()
        
        # Clean up temporary directory
        if os.path.exists(self.test_config_dir):
            shutil.rmtree(self.test_config_dir)
        
        # Clear active connections
        ACTIVE_CONNECTIONS.clear()

    def test_should_return_list_of_connections_when_no_active_connections(self):
        """Test listing connections when no connections are active."""
        # given
        # No active connections (setUp ensures empty state)
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", {"operation": "list"}))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": True,
                "total_connections": 0,
                "connections": {}
            }, indent=2),
            result[0].text
        )

    def test_should_fail_server_start_when_missing_required_parameters(self):
        """Test server start fails with missing required parameters."""
        # given
        invalid_params = {"operation": "server_start"}
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", invalid_params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": False,
                "error": "'name' parameter is required"
            }, indent=2),
            result[0].text
        )

    def test_should_fail_server_start_when_invalid_port_range(self):
        """Test server start fails with invalid port range."""
        # given
        invalid_params = {
            "operation": "server_start",
            "name": "test-server",
            "port": 999
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", invalid_params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": False,
                "error": "Port must be between 1000 and 65535"
            }, indent=2),
            result[0].text
        )

    @patch('tool._start_websocket_server')
    def test_should_start_server_successfully_when_valid_parameters(self, mock_start_server):
        """Test successful server start with valid parameters."""
        # given
        mock_start_server.return_value = {
            "server_id": "ws_server_001",
            "bind_address": "localhost:8080",
            "started_at": "2025-08-21T14:30:00.000Z"
        }
        
        params = {
            "operation": "server_start",
            "name": "test-server",
            "port": 8080,
            "path": "/ws"
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        expected_response = {
            "success": True,
            "message": "WebSocket server 'test-server' started successfully",
            "connection_type": "server",
            "endpoint": "ws://localhost:8080/ws",
            "config": {
                "name": "test-server",
                "type": "server",
                "port": 8080,
                "path": "/ws",
                "bind_host": "localhost",
                "protocol": "ws",
                "subprotocols": [],
                "max_connections": 100,
                "message_size_limit": 1048576,
                "auth": {"type": "none"},
                "ssl": {"enabled": False},
                "connection_handling": {
                    "heartbeat_interval": 30,
                    "connection_timeout": 300,
                    "auto_cleanup": True
                },
                "rate_limiting": {
                    "messages_per_minute": 60,
                    "burst_limit": 10
                },
                "event_handlers": {},
                "auto_responses": {},
                "status": "running",
                "clients": {},
                "metrics": {
                    "total_connections": 0,
                    "active_connections": 0,
                    "total_messages": 0
                },
                "server_info": {
                    "server_id": "ws_server_001",
                    "bind_address": "localhost:8080",
                    "started_at": "2025-08-21T14:30:00.000Z"
                }
            },
            "config_source": "inline"
        }
        
        # Parse result and remove dynamic fields for comparison
        result_data = json.loads(result[0].text)
        if "config" in result_data and "created_at" in result_data["config"]:
            del result_data["config"]["created_at"]
        if "config" in result_data and "metrics" in result_data["config"] and "started_at" in result_data["config"]["metrics"]:
            del result_data["config"]["metrics"]["started_at"]
        
        self.assertEqual(
            json.dumps(expected_response, indent=2),
            json.dumps(result_data, indent=2)
        )

    def test_should_fail_server_stop_when_connection_not_found(self):
        """Test server stop fails when connection doesn't exist."""
        # given
        params = {
            "operation": "server_stop",
            "name": "nonexistent-server"
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": False,
                "error": "WebSocket connection 'nonexistent-server' not found"
            }, indent=2),
            result[0].text
        )

    def test_should_fail_client_connect_when_missing_url(self):
        """Test client connect fails with missing URL parameter."""
        # given
        params = {
            "operation": "client_connect",
            "name": "test-client"
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": False,
                "error": "'url' parameter is required"
            }, indent=2),
            result[0].text
        )

    @patch('tool._start_websocket_client')
    def test_should_connect_client_successfully_when_valid_parameters(self, mock_start_client):
        """Test successful client connection with valid parameters."""
        # given
        mock_start_client.return_value = {
            "connected": True,
            "client_id": "ws_client_001",
            "connected_at": "2025-08-21T14:30:00.000Z"
        }
        
        params = {
            "operation": "client_connect",
            "name": "test-client",
            "url": "ws://localhost:8080/ws"
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        expected_response = {
            "success": True,
            "message": "WebSocket client 'test-client' connected",
            "connection_type": "client",
            "url": "ws://localhost:8080/ws",
            "config": {
                "name": "test-client",
                "type": "client",
                "url": "ws://localhost:8080/ws",
                "subprotocol": None,
                "auth": {"type": "none"},
                "connection_handling": {
                    "auto_reconnect": True,
                    "max_reconnect_attempts": 5,
                    "backoff_strategy": "exponential",
                    "heartbeat_enabled": True,
                    "heartbeat_message": {"type": "ping"}
                },
                "message_handlers": {},
                "status": "connected",
                "metrics": {
                    "connection_attempts": 0,
                    "total_messages_sent": 0,
                    "total_messages_received": 0,
                    "last_activity": None
                },
                "client_info": {
                    "connected": True,
                    "client_id": "ws_client_001",
                    "connected_at": "2025-08-21T14:30:00.000Z"
                }
            },
            "config_source": "inline"
        }
        
        # Parse result and remove dynamic fields for comparison
        result_data = json.loads(result[0].text)
        if "config" in result_data and "created_at" in result_data["config"]:
            del result_data["config"]["created_at"]
        
        self.assertEqual(
            json.dumps(expected_response, indent=2),
            json.dumps(result_data, indent=2)
        )

    def test_should_fail_client_send_when_connection_not_found(self):
        """Test client send fails when connection doesn't exist."""
        # given
        params = {
            "operation": "client_send",
            "name": "nonexistent-client",
            "message": {"type": "test", "data": "hello"}
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": False,
                "error": "WebSocket connection 'nonexistent-client' not found"
            }, indent=2),
            result[0].text
        )

    def test_should_fail_client_send_when_connection_is_not_client(self):
        """Test client send fails when connection is not a client type."""
        # given
        ACTIVE_CONNECTIONS["test-server"] = {
            "type": "server",
            "name": "test-server"
        }
        
        params = {
            "operation": "client_send",
            "name": "test-server",
            "message": {"type": "test"}
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": False,
                "error": "Connection 'test-server' is not a client"
            }, indent=2),
            result[0].text
        )

    def test_should_fail_broadcast_when_missing_message(self):
        """Test broadcast fails when message parameter is missing."""
        # given
        params = {
            "operation": "broadcast",
            "name": "test-server"
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": False,
                "error": "'message' parameter is required"
            }, indent=2),
            result[0].text
        )

    @patch('tool._broadcast_to_clients')
    def test_should_broadcast_successfully_when_valid_server(self, mock_broadcast):
        """Test successful message broadcast to server clients."""
        # given
        mock_broadcast.return_value = {
            "sent_count": 3,
            "failed_count": 0,
            "total_clients": 3
        }
        
        ACTIVE_CONNECTIONS["test-server"] = {
            "type": "server",
            "name": "test-server",
            "metrics": {"total_messages": 0}
        }
        
        params = {
            "operation": "broadcast",
            "name": "test-server",
            "message": {"type": "announcement", "text": "Hello everyone!"}
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": True,
                "message": "Message broadcasted to 3 clients",
                "server_name": "test-server",
                "sent_count": 3,
                "failed_count": 0,
                "total_clients": 3
            }, indent=2),
            result[0].text
        )

    def test_should_return_status_when_connection_exists(self):
        """Test getting status of existing connection."""
        # given
        ACTIVE_CONNECTIONS["test-server"] = {
            "type": "server",
            "name": "test-server",
            "status": "running",
            "created_at": "2025-08-21T14:30:00.000Z",
            "port": 8080,
            "path": "/ws",
            "bind_host": "localhost",
            "ssl": {"enabled": False},
            "clients": {},
            "metrics": {
                "total_connections": 5,
                "active_connections": 2,
                "total_messages": 47
            }
        }
        
        params = {
            "operation": "status",
            "name": "test-server",
            "include_metrics": True
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": True,
                "connection_status": {
                    "name": "test-server",
                    "type": "server",
                    "status": "running",
                    "created_at": "2025-08-21T14:30:00.000Z",
                    "metrics": {
                        "total_connections": 5,
                        "active_connections": 2,
                        "total_messages": 47
                    },
                    "endpoint": "ws://localhost:8080/ws",
                    "active_clients": 0
                }
            }, indent=2),
            result[0].text
        )

    def test_should_fail_status_when_connection_not_found(self):
        """Test status fails when connection doesn't exist."""
        # given
        params = {
            "operation": "status",
            "name": "nonexistent-connection"
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": False,
                "error": "WebSocket connection 'nonexistent-connection' not found"
            }, indent=2),
            result[0].text
        )

    @patch('tool._broadcast_to_clients')
    def test_should_test_server_connection_successfully_when_connection_exists(self, mock_broadcast):
        """Test successful server connection testing."""
        # given
        mock_broadcast.return_value = {
            "sent_count": 2,
            "failed_count": 0,
            "total_clients": 2
        }
        
        ACTIVE_CONNECTIONS["test-server"] = {
            "type": "server",
            "name": "test-server"
        }
        
        params = {
            "operation": "test",
            "name": "test-server",
            "test_data": {"type": "test_message", "content": "Test broadcast"}
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": True,
                "message": "Test message sent to 2 clients",
                "connection_name": "test-server",
                "test_data": {"type": "test_message", "content": "Test broadcast"},
                "sent_count": 2,
                "failed_count": 0
            }, indent=2),
            result[0].text
        )

    @patch('tool._send_client_message')
    def test_should_test_client_connection_successfully_when_connection_exists(self, mock_send):
        """Test successful client connection testing."""
        # given
        mock_send.return_value = {
            "success": True,
            "message_id": "msg_001"
        }
        
        ACTIVE_CONNECTIONS["test-client"] = {
            "type": "client",
            "name": "test-client"
        }
        
        params = {
            "operation": "test",
            "name": "test-client"
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": True,
                "message": "Test message sent",
                "connection_name": "test-client",
                "test_data": {"type": "test", "message": "Hello WebSocket!"},
                "error": None
            }, indent=2),
            result[0].text
        )

    def test_should_return_multiple_connections_when_list_with_active_connections(self):
        """Test listing multiple active connections with detailed information."""
        # given
        ACTIVE_CONNECTIONS.update({
            "server-1": {
                "type": "server",
                "name": "server-1",
                "status": "running",
                "created_at": "2025-08-21T14:30:00.000Z",
                "port": 8080,
                "path": "/ws",
                "clients": {"client1": {}, "client2": {}},
                "metrics": {"total_connections": 5}
            },
            "client-1": {
                "type": "client",
                "name": "client-1",
                "status": "connected",
                "created_at": "2025-08-21T14:35:00.000Z",
                "url": "ws://external.com/ws",
                "metrics": {"last_activity": "2025-08-21T14:40:00.000Z"}
            }
        })
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", {"operation": "list"}))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": True,
                "total_connections": 2,
                "connections": {
                    "server-1": {
                        "name": "server-1",
                        "type": "server",
                        "status": "running",
                        "created_at": "2025-08-21T14:30:00.000Z",
                        "port": 8080,
                        "path": "/ws",
                        "active_clients": 2,
                        "total_connections": 5
                    },
                    "client-1": {
                        "name": "client-1",
                        "type": "client",
                        "status": "connected",
                        "created_at": "2025-08-21T14:35:00.000Z",
                        "url": "ws://external.com/ws",
                        "last_activity": "2025-08-21T14:40:00.000Z"
                    }
                }
            }, indent=2),
            result[0].text
        )

    def test_should_fail_when_unknown_operation_provided(self):
        """Test tool fails gracefully with unknown operation."""
        # given
        params = {
            "operation": "unknown_operation",
            "name": "test-connection"
        }
        
        # when
        result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": False,
                "error": "Unknown operation: unknown_operation"
            }, indent=2),
            result[0].text
        )

    def test_should_handle_ssl_configuration_in_server_start(self):
        """Test server start with SSL configuration creates proper endpoint URL."""
        # given
        with patch('tool._start_websocket_server') as mock_start_server:
            mock_start_server.return_value = {
                "server_id": "wss_server_001",
                "bind_address": "0.0.0.0:8443"
            }
            
            params = {
                "operation": "server_start",
                "name": "secure-server",
                "port": 8443,
                "path": "/secure-ws",
                "bind_host": "0.0.0.0",
                "protocol": "wss",
                "ssl": {
                    "enabled": True,
                    "cert_file": "/etc/ssl/certs/server.crt",
                    "key_file": "/etc/ssl/private/server.key"
                }
            }
            
            # when
            result = asyncio.run(run_tool("lng_websocket_server", params))
            
            # then
            result_data = json.loads(result[0].text)
            self.assertEqual("wss://0.0.0.0:8443/secure-ws", result_data["endpoint"])
            self.assertEqual(True, result_data["config"]["ssl"]["enabled"])

    def test_should_handle_authentication_configuration_masking_in_output(self):
        """Test authentication configuration is properly masked in tool output."""
        # given
        with patch('tool._start_websocket_server') as mock_start_server:
            mock_start_server.return_value = {"server_id": "auth_server_001"}
            
            params = {
                "operation": "server_start",
                "name": "auth-server",
                "port": 8080,
                "auth": {
                    "type": "bearer_token",
                    "token": "secret-token-12345",
                    "origin_whitelist": ["https://trusted.com"]
                }
            }
            
            # when
            result = asyncio.run(run_tool("lng_websocket_server", params))
            
            # then
            result_data = json.loads(result[0].text)
            self.assertEqual("sec***345", result_data["config"]["auth"]["token"])
            self.assertIn("origin_whitelist", result_data["config"]["auth"])

    def test_should_disconnect_client_successfully_when_connection_exists_case_cleanup(self):
        """Test successful client disconnection with proper cleanup."""
        # given
        mock_client = MagicMock()
        mock_client.disconnect = AsyncMock()
        
        ACTIVE_CONNECTIONS["test-client"] = {
            "type": "client",
            "name": "test-client",
            "_client_instance": mock_client
        }
        
        params = {
            "operation": "client_disconnect",
            "name": "test-client"
        }
        
        # when
        with patch('tool._stop_connection_by_name', new_callable=AsyncMock) as mock_stop:
            result = asyncio.run(run_tool("lng_websocket_server", params))
        
        # then
        self.assertEqual(
            json.dumps({
                "success": True,
                "message": "WebSocket client 'test-client' disconnected successfully"
            }, indent=2),
            result[0].text
        )

    @patch('tool._start_websocket_server')
    @patch('tool._start_websocket_client')
    @patch('tool._send_client_message')
    @patch('tool._broadcast_to_clients')
    def test_should_create_server_and_client_from_config_files_and_test_communication_then_cleanup(
        self, mock_broadcast, mock_send_message, mock_start_client, mock_start_server
    ):
        """Integration test: Create config files, start server and client, test communication, then cleanup."""
        
        # Create temporary config files
        server_config_file = os.path.join(self.test_config_dir, "test_server_config.json")
        client_config_file = os.path.join(self.test_config_dir, "test_client_config.json")
        
        # Server configuration
        server_config = {
            "name": "integration-test-server",
            "port": 9876,
            "path": "/ws/integration-test",
            "bind_host": "localhost",
            "protocol": "ws",
            "auth": {"type": "none"},
            "ssl": {"enabled": False},
            "connection_handling": {
                "heartbeat_interval": 30,
                "max_connections": 10,
                "auto_cleanup": True
            },
            "event_handlers": {
                "on_connect": [
                    {
                        "tool": "lng_count_words",
                        "params": {"input_text": "Client connected from {! websocket.remote_ip !}"},
                        "output": "connect_stats"
                    }
                ],
                "on_message": [
                    {
                        "tool": "lng_count_words", 
                        "params": {"input_text": "{! websocket.message.content !}"},
                        "output": "message_stats"
                    }
                ]
            }
        }
        
        # Client configuration  
        client_config = {
            "name": "integration-test-client",
            "url": "ws://localhost:9876/ws/integration-test",
            "subprotocol": "test-protocol-v1",
            "auth": {"type": "none"},
            "connection_handling": {
                "auto_reconnect": True,
                "heartbeat_enabled": True,
                "heartbeat_message": {"type": "ping", "timestamp": "{! new Date().toISOString() !}"}
            },
            "message_handlers": {
                "on_message": [
                    {
                        "condition": "{! websocket.message.type === 'echo_request' !}",
                        "tool": "lng_websocket_server",
                        "params": {
                            "operation": "client_send",
                            "name": "integration-test-client",
                            "message": {
                                "type": "echo_response",
                                "original": "{! websocket.message.content !}",
                                "timestamp": "{! new Date().toISOString() !}"
                            }
                        }
                    }
                ]
            }
        }
        
        try:
            # given - Create config files
            with open(server_config_file, 'w', encoding='utf-8') as f:
                json.dump(server_config, f, indent=2, ensure_ascii=False)
            
            with open(client_config_file, 'w', encoding='utf-8') as f:
                json.dump(client_config, f, indent=2, ensure_ascii=False)
            
            # Mock server and client startup responses
            mock_start_server.return_value = {
                "started": True,
                "endpoint": "ws://localhost:9876/ws/integration-test",
                "protocol": "ws",
                "ssl_enabled": False,
                "server_id": "integration_server_001"
            }
            
            mock_start_client.return_value = {
                "connected": True,
                "client_id": "integration_client_001", 
                "connected_at": "2025-08-22T18:45:00.000Z"
            }
            
            mock_send_message.return_value = {
                "success": True,
                "message_id": "msg_integration_001"
            }
            
            mock_broadcast.return_value = {
                "sent_count": 1,
                "failed_count": 0,
                "total_clients": 1
            }
            
            # when - Start server from config file
            server_result = asyncio.run(run_tool("lng_websocket_server", {
                "operation": "server_start",
                "config_file": server_config_file
            }))
            
            # then - Verify server started successfully
            server_data = json.loads(server_result[0].text)
            self.assertTrue(server_data["success"])
            self.assertEqual("integration-test-server", server_data["config"]["name"])
            self.assertEqual(9876, server_data["config"]["port"])
            self.assertEqual("config_file", server_data["config_source"])
            self.assertEqual("ws://localhost:9876/ws/integration-test", server_data["endpoint"])
            
            # when - Start client from config file
            client_result = asyncio.run(run_tool("lng_websocket_server", {
                "operation": "client_connect", 
                "config_file": client_config_file
            }))
            
            # then - Verify client connected successfully
            client_data = json.loads(client_result[0].text)
            self.assertTrue(client_data["success"])
            self.assertEqual("integration-test-client", client_data["config"]["name"])
            self.assertEqual("ws://localhost:9876/ws/integration-test", client_data["config"]["url"])
            self.assertEqual("config_file", client_data["config_source"])
            self.assertEqual("test-protocol-v1", client_data["config"]["subprotocol"])
            
            # when - Test client sending message to server
            send_result = asyncio.run(run_tool("lng_websocket_server", {
                "operation": "client_send",
                "name": "integration-test-client",
                "message": {
                    "type": "hello",
                    "content": "Hello integration test server!",
                    "timestamp": "2025-08-22T18:45:30.000Z"
                }
            }))
            
            # then - Verify message was sent successfully
            send_data = json.loads(send_result[0].text)
            self.assertTrue(send_data["success"])
            self.assertEqual("Message sent", send_data["message"])
            self.assertEqual("integration-test-client", send_data["connection_name"])
            
            # when - Test server broadcasting message to clients
            broadcast_result = asyncio.run(run_tool("lng_websocket_server", {
                "operation": "broadcast",
                "name": "integration-test-server", 
                "message": {
                    "type": "announcement",
                    "content": "Server broadcasting to all clients",
                    "timestamp": "2025-08-22T18:46:00.000Z"
                }
            }))
            
            # then - Verify broadcast was successful
            broadcast_data = json.loads(broadcast_result[0].text)
            self.assertTrue(broadcast_data["success"])
            self.assertEqual("Message broadcasted to 1 clients", broadcast_data["message"])
            self.assertEqual(1, broadcast_data["sent_count"])
            self.assertEqual(0, broadcast_data["failed_count"])
            
            # when - Check connections list
            list_result = asyncio.run(run_tool("lng_websocket_server", {
                "operation": "list"
            }))
            
            # then - Verify both connections are active
            list_data = json.loads(list_result[0].text)
            self.assertTrue(list_data["success"])
            self.assertEqual(2, list_data["total_connections"])
            self.assertIn("integration-test-server", list_data["connections"])
            self.assertIn("integration-test-client", list_data["connections"])
            self.assertEqual("server", list_data["connections"]["integration-test-server"]["type"])
            self.assertEqual("client", list_data["connections"]["integration-test-client"]["type"])
            
            # when - Get detailed status of server with metrics
            server_status_result = asyncio.run(run_tool("lng_websocket_server", {
                "operation": "status",
                "name": "integration-test-server",
                "include_metrics": True
            }))
            
            # then - Verify server status
            server_status_data = json.loads(server_status_result[0].text)
            self.assertTrue(server_status_data["success"])
            self.assertEqual("integration-test-server", server_status_data["connection_status"]["name"])
            self.assertEqual("server", server_status_data["connection_status"]["type"])
            self.assertIn("metrics", server_status_data["connection_status"])
            
            # when - Test server connection
            test_server_result = asyncio.run(run_tool("lng_websocket_server", {
                "operation": "test",
                "name": "integration-test-server",
                "test_data": {
                    "type": "test_broadcast",
                    "content": "Testing server broadcast functionality"
                }
            }))
            
            # then - Verify server test
            test_server_data = json.loads(test_server_result[0].text)
            self.assertTrue(test_server_data["success"])
            self.assertEqual("Test message sent to 1 clients", test_server_data["message"])
            
            # when - Test client connection
            test_client_result = asyncio.run(run_tool("lng_websocket_server", {
                "operation": "test", 
                "name": "integration-test-client",
                "test_data": {
                    "type": "test_message",
                    "content": "Testing client send functionality"
                }
            }))
            
            # then - Verify client test
            test_client_data = json.loads(test_client_result[0].text)
            self.assertTrue(test_client_data["success"])
            self.assertEqual("Test message sent", test_client_data["message"])
            
        finally:
            # Cleanup - Stop client and server connections
            try:
                asyncio.run(run_tool("lng_websocket_server", {
                    "operation": "client_disconnect",
                    "name": "integration-test-client"
                }))
            except:
                pass  # Ignore cleanup errors
            
            try:
                asyncio.run(run_tool("lng_websocket_server", {
                    "operation": "server_stop",
                    "name": "integration-test-server"
                }))
            except:
                pass  # Ignore cleanup errors
            
            # Remove config files
            for config_file in [server_config_file, client_config_file]:
                if os.path.exists(config_file):
                    try:
                        os.remove(config_file)
                    except:
                        pass  # Ignore file cleanup errors
            
            # Verify cleanup - connections should be removed
            final_list_result = asyncio.run(run_tool("lng_websocket_server", {
                "operation": "list"
            }))
            
            final_list_data = json.loads(final_list_result[0].text)
            self.assertTrue(final_list_data["success"])
            # Should not contain our test connections anymore
            self.assertNotIn("integration-test-server", final_list_data["connections"])
            self.assertNotIn("integration-test-client", final_list_data["connections"])


if __name__ == '__main__':
    # Enable running tests directly
    unittest.main(verbosity=2)
