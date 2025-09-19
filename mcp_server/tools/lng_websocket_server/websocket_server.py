import asyncio
import websockets
import ssl
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import parse_qs, urlparse
from websockets.server import WebSocketServerProtocol

from ...pipeline.expressions import evaluate_expression, substitute_in_object
from ...logging_config import setup_logging

logger = setup_logging('mcp_server', logging.DEBUG)

class WebSocketServerManager:
    """WebSocket Server Manager with pipeline integration."""
    
    def __init__(self, config: dict):
        self.config = config
        self.name = config["name"]
        self.port = config["port"]
        self.path = config["path"]
        self.bind_host = config["bind_host"]
        
        # Server instance and clients
        self.server = None
        self.clients: Dict[str, Dict] = {}
        self.client_counter = 0
        
        # Configuration
        self.max_connections = config.get("max_connections", 100)
        self.message_size_limit = config.get("message_size_limit", 1048576)
        self.auth_config = config.get("auth", {"type": "none"})
        self.ssl_config = config.get("ssl", {"enabled": False})
        self.connection_handling = config.get("connection_handling", {})
        self.rate_limiting = config.get("rate_limiting", {})
        self.event_handlers = config.get("event_handlers", {})
        self.auto_responses = config.get("auto_responses", {})
        
        # Setup dedicated logger for this WebSocket endpoint
        self.logger = self._setup_logger()
        
        # Metrics
        self.metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "total_messages": 0,
            "started_at": datetime.now().isoformat(),
            "uptime_seconds": 0
        }
        
        # Expression evaluation - use function instead of class
        
    def _setup_logger(self):
        """Setup dedicated logger for this WebSocket endpoint."""
        from ...logging_config import setup_instance_logger
        instance_logger = setup_instance_logger(self.name, 'websocket')
        
        # Also configure websockets library logger to write to the same file
        websockets_logger = logging.getLogger('websockets')
        websockets_logger.setLevel(logging.WARNING)  # Only warnings and errors
        websockets_logger.handlers.clear()
        websockets_logger.addHandler(instance_logger.handlers[0])  # Use the same file handler
        websockets_logger.propagate = False
        
        return instance_logger
        
    def _safe_parse_datetime(self, date_value, fallback=None):
        """
        Safely parse datetime from various formats.
        
        Args:
            date_value: Can be datetime object, ISO string, or None
            fallback: Fallback datetime if parsing fails (defaults to now)
            
        Returns:
            datetime: Parsed datetime object
        """
        if fallback is None:
            fallback = datetime.now()
            
        if isinstance(date_value, datetime):
            return date_value
        elif isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value)
            except ValueError:
                return fallback
        else:
            return fallback
        
        # Heartbeat and cleanup tasks
        self.heartbeat_task = None
        self.cleanup_task = None
        
    async def start(self) -> dict:
        """Start WebSocket server."""
        try:
            # Setup SSL context if enabled
            ssl_context = None
            if self.ssl_config.get("enabled"):
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(
                    certfile=self.ssl_config["cert_file"],
                    keyfile=self.ssl_config["key_file"]
                )
                self.logger.info(f"SSL enabled for WebSocket server '{self.name}'")
            
            # Start WebSocket server
            self.server = await websockets.serve(
                self.handle_client,
                self.bind_host,
                self.port,
                ssl=ssl_context,
                subprotocols=self.config.get("subprotocols", []),
                max_size=self.message_size_limit,
                max_queue=32,
                close_timeout=10,
                process_request=self.process_request
            )
            
            # Start background tasks
            if self.connection_handling.get("heartbeat_interval", 0) > 0:
                self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
            
            if self.connection_handling.get("auto_cleanup", True):
                self.cleanup_task = asyncio.create_task(self.cleanup_loop())
            
            protocol = "wss" if ssl_context else "ws"
            endpoint = f"{protocol}://{self.bind_host}:{self.port}{self.path}"
            
            self.logger.info(f"WebSocket server '{self.name}' started on {endpoint}")
            
            return {
                "started": True,
                "endpoint": endpoint,
                "protocol": protocol,
                "ssl_enabled": ssl_context is not None,
                "subprotocols": self.config.get("subprotocols", [])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket server '{self.name}': {e}")
            raise
    
    async def stop(self):
        """Stop WebSocket server."""
        try:
            # Stop background tasks
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
                    
            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Close all client connections
            if self.clients:
                disconnect_tasks = []
                for client_id, client_info in self.clients.items():
                    if "websocket" in client_info:
                        disconnect_tasks.append(
                            self.close_client_connection(client_id, "Server shutdown")
                        )
                
                if disconnect_tasks:
                    await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            
            # Stop server
            if self.server:
                self.server.close()
                await self.server.wait_closed()
                
            self.logger.info(f"WebSocket server '{self.name}' stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping WebSocket server '{self.name}': {e}")
    
    async def process_request(self, connection, request):
        """Process WebSocket upgrade request (for custom paths)."""
        # Extract path from request object
        path = getattr(request, 'path', '/ws')
        
        # Store path using connection ID (thread-safe approach)
        connection_id = id(connection)
        if not hasattr(self, '_connection_paths'):
            self._connection_paths = {}
        self._connection_paths[connection_id] = path
        
        if path.startswith(self.path):
            return None  # Accept the request
        else:
            # Return HTTP response for rejected paths
            from websockets.datastructures import Headers
            return 404, Headers(), b"Not Found"
    
    async def handle_client(self, websocket):
        """Handle new WebSocket client connection."""
        client_id = None
    async def handle_client(self, websocket):
        """Handle new WebSocket client connection."""
        client_id = None
        try:
            # Get path from stored request using connection ID (thread-safe)
            connection_id = id(websocket)
            path = getattr(self, '_connection_paths', {}).pop(connection_id, None) or getattr(websocket, 'path', '/ws')
            
            # Parse query parameters from WebSocket URL
            url_parts = urlparse(path)
            query_params = parse_qs(url_parts.query)
            # Flatten query params (take first value if multiple)
            query_params = {k: v[0] if v else '' for k, v in query_params.items()}
            
            # Generate unique client ID
            self.client_counter += 1
            client_id = f"ws_client_{self.client_counter:06d}"
            
            # Check connection limit
            if len(self.clients) >= self.max_connections:
                await websocket.close(code=1013, reason="Server overloaded")
                self.logger.warning(f"Connection limit reached, rejected client {client_id}")
                return
            
            # Authenticate client
            auth_result = await self.authenticate_client(websocket, client_id)
            if not auth_result["authenticated"]:
                await websocket.close(code=1008, reason=auth_result["reason"])
                self.logger.warning(f"Authentication failed for client {client_id}: {auth_result['reason']}")
                return
            
            # Create client info
            client_info = {
                "client_id": client_id,
                "websocket": websocket,
                "remote_ip": websocket.remote_address[0] if websocket.remote_address else "unknown",
                "user_agent": getattr(websocket, 'request_headers', {}).get("User-Agent", "unknown"),
                "subprotocol": getattr(websocket, 'subprotocol', None),
                "path": path,
                "query_params": query_params,
                "connected_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "authenticated": auth_result["authenticated"],
                "auth_data": auth_result.get("auth_data", {}),
                "message_count": 0,
                "bytes_received": 0,
                "bytes_sent": 0,
                "rate_limit_reset": datetime.now(),
                "rate_limit_count": 0
            }
            
            # Store client
            self.clients[client_id] = client_info
            self.metrics["total_connections"] += 1
            self.metrics["active_connections"] = len(self.clients)
            
            # Update parent config clients
            if hasattr(self.config, 'clients'):
                self.config["clients"][client_id] = {
                    "connected_at": client_info["connected_at"],
                    "remote_ip": client_info["remote_ip"],
                    "authenticated": client_info["authenticated"]
                }
            
            self.logger.info(f"Client {client_id} connected from {client_info['remote_ip']}")
            
            # Execute on_connect handlers
            await self.execute_event_handlers("on_connect", client_info)
            
            # Handle messages
            async for message in websocket:
                try:
                    await self.handle_message(client_id, message)
                except Exception as e:
                    self.logger.error(f"Error handling message from client {client_id}: {e}")
                    self.logger.error(traceback.format_exc())
        
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client {client_id} disconnected normally")
        except Exception as e:
            self.logger.error(f"Error handling client {client_id}: {e}")
            self.logger.error(traceback.format_exc())
        finally:
            # Clean up client
            if client_id and client_id in self.clients:
                client_info = self.clients[client_id]
                await self.execute_event_handlers("on_disconnect", client_info)
                del self.clients[client_id]
                self.metrics["active_connections"] = len(self.clients)
                
                # Update parent config
                if hasattr(self.config, 'clients') and client_id in self.config["clients"]:
                    del self.config["clients"][client_id]
                
                self.logger.info(f"Client {client_id} cleaned up")
    
    async def authenticate_client(self, websocket, client_id: str) -> dict:
        """Authenticate WebSocket client."""
        try:
            auth_config = self.auth_config
            auth_type = auth_config.get("type", "none")
            
            if auth_type == "none":
                return {"authenticated": True}
            
            elif auth_type == "bearer_token":
                # Check Authorization header
                headers = getattr(websocket, 'request_headers', {})
                auth_header = headers.get("Authorization", "")
                if not auth_header.startswith("Bearer "):
                    return {"authenticated": False, "reason": "Missing Bearer token"}
                
                token = auth_header[7:]  # Remove "Bearer " prefix
                expected_token = auth_config.get("token", "")
                
                if token != expected_token:
                    return {"authenticated": False, "reason": "Invalid token"}
                
                return {"authenticated": True, "auth_data": {"token_type": "bearer"}}
            
            elif auth_type == "query_param":
                # Check URL query parameters
                url_parts = urlparse(websocket.path)
                query_params = parse_qs(url_parts.query)
                
                param_name = auth_config.get("param_name", "token")
                expected_token = auth_config.get("token", "")
                
                if param_name not in query_params:
                    return {"authenticated": False, "reason": f"Missing {param_name} parameter"}
                
                token = query_params[param_name][0]
                if token != expected_token:
                    return {"authenticated": False, "reason": "Invalid token"}
                
                return {"authenticated": True, "auth_data": {"token_type": "query_param"}}
            
            elif auth_type == "header":
                # Check custom header
                header_name = auth_config.get("header_name", "X-Auth-Token")
                headers = getattr(websocket, 'request_headers', {})
                token = headers.get(header_name, "")
                expected_token = auth_config.get("token", "")
                
                if not token:
                    return {"authenticated": False, "reason": f"Missing {header_name} header"}
                
                if token != expected_token:
                    return {"authenticated": False, "reason": "Invalid token"}
                
                return {"authenticated": True, "auth_data": {"token_type": "header"}}
            
            else:
                return {"authenticated": False, "reason": f"Unknown auth type: {auth_type}"}
            
        except Exception as e:
            self.logger.error(f"Authentication error for client {client_id}: {e}")
            return {"authenticated": False, "reason": "Authentication error"}
    
    async def handle_message(self, client_id: str, message):
        """Handle incoming message from client."""
        try:
            client_info = self.clients.get(client_id)
            if not client_info:
                return
            
            # Check rate limiting
            rate_limit_check = await self.check_rate_limit(client_id)
            if not rate_limit_check["allowed"]:
                await self.send_to_client(client_id, {
                    "type": "error",
                    "message": "Rate limit exceeded",
                    "retry_after": rate_limit_check["retry_after"]
                })
                return
            
            # Update client activity
            client_info["last_activity"] = datetime.now().isoformat()
            client_info["message_count"] += 1
            
            # Parse message
            if isinstance(message, str):
                message_data = {"type": "text", "content": message}
                try:
                    # Try to parse as JSON
                    parsed = json.loads(message)
                    if isinstance(parsed, dict):
                        message_data = parsed
                except:
                    pass  # Keep as text message
            else:
                message_data = {"type": "binary", "content": message, "size": len(message)}
            
            client_info["bytes_received"] += len(message) if isinstance(message, (str, bytes)) else 0
            self.metrics["total_messages"] += 1
            
            # Check auto responses first
            auto_response = await self.check_auto_responses(message_data, client_info)
            if auto_response:
                await self.send_to_client(client_id, auto_response)
            
            # Execute message handlers
            await self.execute_event_handlers("on_message", client_info, message_data)
            
        except Exception as e:
            self.logger.error(f"Error handling message from client {client_id}: {e}")
            self.logger.error(traceback.format_exc())
    
    async def check_rate_limit(self, client_id: str) -> dict:
        """Check rate limiting for client."""
        try:
            if not self.rate_limiting:
                return {"allowed": True}
            
            client_info = self.clients.get(client_id)
            if not client_info:
                return {"allowed": False, "reason": "Client not found"}
            
            messages_per_minute = self.rate_limiting.get("messages_per_minute", 60)
            burst_limit = self.rate_limiting.get("burst_limit", 10)
            
            now = datetime.now()
            
            # Reset rate limit counter if minute passed
            rate_limit_reset = client_info.get("rate_limit_reset", now.isoformat())
            reset_time = self._safe_parse_datetime(rate_limit_reset, now)
            
            if (now - reset_time).seconds >= 60:
                client_info["rate_limit_count"] = 0
                client_info["rate_limit_reset"] = now.isoformat()
            
            # Check limits
            if client_info["rate_limit_count"] >= messages_per_minute:
                return {
                    "allowed": False,
                    "reason": "Per-minute limit exceeded",
                    "retry_after": 60
                }
            
            client_info["rate_limit_count"] += 1
            return {"allowed": True}
            
        except Exception as e:
            self.logger.error(f"Rate limiting error for client {client_id}: {e}")
            return {"allowed": True}  # Allow on error to prevent blocking
    
    async def check_auto_responses(self, message_data: dict, client_info: dict) -> Optional[dict]:
        """Check for automatic responses to messages."""
        try:
            for response_name, response_config in self.auto_responses.items():
                condition = response_config.get("condition")
                if not condition:
                    continue
                
                # Build context for condition evaluation
                context = {
                    "websocket": {
                        "client_id": client_info["client_id"],
                        "message": message_data,
                        "remote_ip": client_info["remote_ip"],
                        "authenticated": client_info["authenticated"]
                    },
                    "message": message_data
                }
                
                # Evaluate condition
                condition_result = evaluate_expression(condition, context)
                if condition_result:
                    response = response_config.get("response", {})
                    # Evaluate response content
                    return substitute_in_object(response, context)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Auto response check error: {e}")
            return None
    
    async def execute_event_handlers(self, event_type: str, client_info: dict, message_data: dict = None):
        """Execute pipeline handlers for WebSocket events."""
        try:
            handlers = self.event_handlers.get(event_type, [])
            if not handlers:
                return
            
            # Build context for pipeline execution
            context = {
                "websocket": {
                    "timestamp": datetime.now().isoformat(),
                    "connection_type": "server",
                    "connection_name": self.name,
                    "client_id": client_info["client_id"],
                    "remote_ip": client_info["remote_ip"],
                    "user_agent": client_info["user_agent"],
                    "subprotocol": client_info["subprotocol"],
                    "path": client_info.get("path", ""),
                    "query_params": client_info.get("query_params", {}),
                    "authenticated": client_info["authenticated"],
                    "connected_at": client_info["connected_at"],
                    "message_count": client_info["message_count"]
                },
                "connection": {
                    "total_messages": client_info["message_count"],
                    "bytes_received": client_info["bytes_received"],
                    "bytes_sent": client_info["bytes_sent"],
                    "last_activity": client_info["last_activity"]
                }
            }
            
            if message_data:
                context["websocket"]["message"] = message_data
            
            # Execute handlers
            for handler in handlers:
                try:
                    # Use lng_batch_run to execute pipeline
                    from ...tools.lng_batch_run.tool import run_tool as run_batch_tool
                    
                    # Execute pipeline step
                    if "tool" in handler:
                        # Single tool execution
                        await self.execute_single_handler(handler, context)
                    elif "pipeline" in handler:
                        # Full pipeline execution
                        pipeline_params = {
                            "pipeline": handler["pipeline"],
                            "context_fields": ["websocket", "connection"]
                        }
                        # Add context variables
                        for key, value in context.items():
                            pipeline_params[f"context_{key}"] = value
                        
                        await run_batch_tool("lng_batch_run", pipeline_params)
                        
                except Exception as e:
                    self.logger.error(f"Error executing {event_type} handler: {e}")
                    self.logger.error(traceback.format_exc())
        
        except Exception as e:
            self.logger.error(f"Error in event handler execution: {e}")
            self.logger.error(traceback.format_exc())
    
    async def execute_single_handler(self, handler: dict, context: dict):
        """Execute a single handler tool."""
        try:
            tool_name = handler.get("tool")
            tool_params = handler.get("params", {})
            
            # Evaluate parameters with context
            evaluated_params = substitute_in_object(tool_params, context)
            
            # Import and execute tool dynamically
            from ...tools.tool_registry import run_tool
            
            try:
                await run_tool(tool_name, evaluated_params)
            except ValueError as e:
                self.logger.warning(f"Tool '{tool_name}' not found for handler execution: {e}")
            except Exception as e:
                self.logger.error(f"Error running tool '{tool_name}': {e}")
                
        except Exception as e:
            self.logger.error(f"Error executing single handler: {e}")
            self.logger.error(traceback.format_exc())
    
    async def send_to_client(self, client_id: str, message: Any) -> bool:
        """Send message to specific client."""
        try:
            client_info = self.clients.get(client_id)
            if not client_info or "websocket" not in client_info:
                return False
            
            websocket = client_info["websocket"]
            
            # Convert message to appropriate format
            if isinstance(message, dict):
                message_text = json.dumps(message, ensure_ascii=False)
            elif isinstance(message, str):
                message_text = message
            else:
                message_text = str(message)
            
            await websocket.send(message_text)
            
            # Update client metrics
            client_info["bytes_sent"] += len(message_text)
            client_info["last_activity"] = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending message to client {client_id}: {e}")
            return False
    
    async def broadcast_message(self, message: Any, filter_config: dict = None) -> dict:
        """Broadcast message to all or filtered clients."""
        sent_count = 0
        failed_count = 0
        total_clients = len(self.clients)
        
        try:
            # Apply filters if specified
            target_clients = await self.filter_clients(filter_config)
            
            # Send to each target client
            for client_id in target_clients:
                try:
                    success = await self.send_to_client(client_id, message)
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to send to client {client_id}: {e}")
                    failed_count += 1
            
            self.logger.info(f"Broadcast completed: {sent_count} sent, {failed_count} failed, {total_clients} total")
            
            return {
                "sent_count": sent_count,
                "failed_count": failed_count,
                "total_clients": total_clients,
                "target_clients": len(target_clients)
            }
            
        except Exception as e:
            self.logger.error(f"Error in broadcast: {e}")
            return {"sent_count": 0, "failed_count": total_clients, "total_clients": total_clients}
    
    async def filter_clients(self, filter_config: dict = None) -> List[str]:
        """Filter clients based on configuration."""
        try:
            if not filter_config:
                return list(self.clients.keys())
            
            target_clients = []
            
            # Include/exclude specific clients
            include_clients = filter_config.get("include_clients", [])
            exclude_clients = filter_config.get("exclude_clients", [])
            
            if include_clients:
                # Only include specified clients
                for client_id in include_clients:
                    if client_id in self.clients:
                        target_clients.append(client_id)
            else:
                # Include all clients
                target_clients = list(self.clients.keys())
            
            # Exclude specified clients
            if exclude_clients:
                target_clients = [cid for cid in target_clients if cid not in exclude_clients]
            
            # Apply condition filter
            condition = filter_config.get("condition")
            if condition:
                filtered_clients = []
                for client_id in target_clients:
                    client_info = self.clients[client_id]
                    
                    # Build context for condition
                    context = {
                        "client": {
                            "client_id": client_id,
                            "remote_ip": client_info["remote_ip"],
                            "authenticated": client_info["authenticated"],
                            "message_count": client_info["message_count"],
                            "connected_at": client_info["connected_at"]
                        }
                    }
                    
                    # Evaluate condition
                    condition_result = evaluate_expression(condition, context)
                    if condition_result:
                        filtered_clients.append(client_id)
                
                target_clients = filtered_clients
            
            return target_clients
            
        except Exception as e:
            self.logger.error(f"Error filtering clients: {e}")
            return list(self.clients.keys())
    
    async def close_client_connection(self, client_id: str, reason: str = "Connection closed"):
        """Close specific client connection."""
        try:
            client_info = self.clients.get(client_id)
            if client_info and "websocket" in client_info:
                await client_info["websocket"].close(code=1000, reason=reason)
                self.logger.info(f"Closed connection for client {client_id}: {reason}")
        except Exception as e:
            self.logger.error(f"Error closing client {client_id}: {e}")
    
    async def heartbeat_loop(self):
        """Background task for sending heartbeats to clients."""
        try:
            heartbeat_interval = self.connection_handling.get("heartbeat_interval", 30)
            
            while True:
                await asyncio.sleep(heartbeat_interval)
                
                # Send ping to all clients
                disconnected_clients = []
                for client_id, client_info in self.clients.items():
                    try:
                        if "websocket" in client_info:
                            await client_info["websocket"].ping()
                    except Exception as e:
                        self.logger.warning(f"Heartbeat failed for client {client_id}: {e}")
                        disconnected_clients.append(client_id)
                
                # Clean up disconnected clients
                for client_id in disconnected_clients:
                    await self.close_client_connection(client_id, "Heartbeat failed")
                
        except asyncio.CancelledError:
            self.logger.info("Heartbeat loop cancelled")
        except Exception as e:
            self.logger.error(f"Heartbeat loop error: {e}")
    
    async def cleanup_loop(self):
        """Background task for cleaning up stale connections."""
        try:
            timeout_seconds = self.connection_handling.get("connection_timeout", 300)
            
            while True:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.now()
                stale_clients = []
                
                for client_id, client_info in self.clients.items():
                    try:
                        last_activity = client_info.get("last_activity", now.isoformat())
                        # Ensure last_activity is a string
                        if isinstance(last_activity, datetime):
                            last_activity = last_activity.isoformat()
                        elif not isinstance(last_activity, str):
                            last_activity = now.isoformat()
                        
                        last_activity_dt = self._safe_parse_datetime(last_activity, now)
                        if (now - last_activity_dt).seconds > timeout_seconds:
                            stale_clients.append(client_id)
                    except Exception as e:
                        self.logger.warning(f"Error checking client {client_id} activity: {e}")
                        stale_clients.append(client_id)
                
                # Clean up stale clients
                for client_id in stale_clients:
                    await self.close_client_connection(client_id, "Connection timeout")
                    self.logger.info(f"Cleaned up stale client {client_id}")
                
                # Update metrics
                started_at = self.metrics.get("started_at", now.isoformat())
                # Ensure started_at is a string
                if isinstance(started_at, datetime):
                    started_at = started_at.isoformat()
                elif not isinstance(started_at, str):
                    started_at = now.isoformat()
                    
                started_at_dt = self._safe_parse_datetime(started_at, now)
                self.metrics["uptime_seconds"] = (now - started_at_dt).seconds
                
        except asyncio.CancelledError:
            self.logger.info("Cleanup loop cancelled")
        except Exception as e:
            self.logger.error(f"Cleanup loop error: {e}")
