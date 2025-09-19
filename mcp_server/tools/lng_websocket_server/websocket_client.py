import asyncio
import websockets
import ssl
import json
import logging
import os
import traceback
from datetime import datetime
from typing import Dict, Optional, Any
from urllib.parse import urlencode, urlparse, parse_qsl

from ...pipeline.expressions import evaluate_expression, substitute_in_object

logger = logging.getLogger('mcp_server.tools.lng_websocket_server.websocket_client')

class WebSocketClientManager:
    """WebSocket Client Manager with auto-reconnection and pipeline integration."""
    
    def __init__(self, config: dict):
        self.config = config
        self.name = config["name"]
        self.url = config["url"]
        self.subprotocol = config.get("subprotocol")
        
        # Client instance and state
        self.websocket = None
        self.connected = False
        self.connecting = False
        self.should_reconnect = True
        
        # Configuration
        self.auth_config = config.get("auth", {"type": "none"})
        self.connection_handling = config.get("connection_handling", {})
        self.message_handlers = config.get("message_handlers", {})
        
        # Connection settings
        self.auto_reconnect = self.connection_handling.get("auto_reconnect", True)
        self.max_reconnect_attempts = self.connection_handling.get("max_reconnect_attempts", 5)
        self.backoff_strategy = self.connection_handling.get("backoff_strategy", "exponential")
        self.heartbeat_enabled = self.connection_handling.get("heartbeat_enabled", True)
        self.heartbeat_message = self.connection_handling.get("heartbeat_message", {"type": "ping"})
        
        # State tracking
        self.connection_attempts = 0
        self.reconnect_attempts = 0
        self.last_connect_time = None
        self.last_disconnect_time = None
        
        # Metrics
        self.metrics = {
            "connection_attempts": 0,
            "successful_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "total_reconnects": 0,
            "last_activity": None,
            "created_at": datetime.now().isoformat()
        }
        
        # Expression evaluation - use functions instead of class
        
        # Background tasks
        self.listen_task = None
        self.heartbeat_task = None
        self.reconnect_task = None
    
    async def connect(self) -> dict:
        """Connect to WebSocket server."""
        try:
            if self.connected or self.connecting:
                return {"connected": self.connected, "message": "Already connected or connecting"}
            
            self.connecting = True
            self.connection_attempts += 1
            self.metrics["connection_attempts"] += 1
            
            # Build connection URL with authentication
            connection_url = await self.build_connection_url()
            
            # Prepare headers
            headers = await self.build_connection_headers()
            
            # Setup SSL context
            ssl_context = self.get_ssl_context()
            
            # Prepare subprotocols
            subprotocols = []
            if self.subprotocol:
                subprotocols.append(self.subprotocol)
            
            logger.info(f"Connecting WebSocket client '{self.name}' to {self.url}")
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                connection_url,
                subprotocols=subprotocols if subprotocols else None,
                extra_headers=headers,
                ssl=ssl_context,
                max_size=1048576,  # 1MB message limit
                max_queue=32,
                close_timeout=10
            )
            
            self.connected = True
            self.connecting = False
            self.reconnect_attempts = 0
            self.last_connect_time = datetime.now().isoformat()
            self.metrics["successful_connections"] += 1
            self.metrics["last_activity"] = self.last_connect_time
            
            # Start background tasks
            self.listen_task = asyncio.create_task(self.listen_loop())
            
            if self.heartbeat_enabled:
                self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
            
            logger.info(f"WebSocket client '{self.name}' connected successfully")
            
            return {
                "connected": True,
                "message": "Connected successfully",
                "url": self.url,
                "subprotocol": self.websocket.subprotocol,
                "connection_time": self.last_connect_time
            }
            
        except Exception as e:
            self.connecting = False
            self.connected = False
            error_msg = f"Failed to connect: {e}"
            logger.error(f"WebSocket client '{self.name}' connection failed: {e}")
            logger.error(traceback.format_exc())
            
            # Schedule reconnection if enabled
            if self.auto_reconnect and self.reconnect_attempts < self.max_reconnect_attempts:
                self.schedule_reconnect()
            
            return {
                "connected": False,
                "error": error_msg,
                "connection_attempts": self.connection_attempts,
                "reconnect_attempts": self.reconnect_attempts
            }
    
    async def disconnect(self):
        """Disconnect WebSocket client."""
        try:
            self.should_reconnect = False
            
            # Cancel background tasks
            if self.listen_task:
                self.listen_task.cancel()
                try:
                    await self.listen_task
                except asyncio.CancelledError:
                    pass
                    
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
                    
            if self.reconnect_task:
                self.reconnect_task.cancel()
                try:
                    await self.reconnect_task
                except asyncio.CancelledError:
                    pass
            
            # Close WebSocket connection
            if self.websocket:
                await self.websocket.close(code=1000, reason="Client disconnecting")
                self.websocket = None
            
            self.connected = False
            self.connecting = False
            self.last_disconnect_time = datetime.now().isoformat()
            
            logger.info(f"WebSocket client '{self.name}' disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket client '{self.name}': {e}")
    
    async def send_message(self, message: Any) -> dict:
        """Send message to WebSocket server."""
        try:
            if not self.connected or not self.websocket:
                return {"success": False, "error": "Not connected"}
            
            # Convert message to appropriate format
            if isinstance(message, dict):
                message_text = json.dumps(message, ensure_ascii=False)
            elif isinstance(message, str):
                message_text = message
            else:
                message_text = str(message)
            
            await self.websocket.send(message_text)
            
            # Update metrics
            self.metrics["total_messages_sent"] += 1
            self.metrics["last_activity"] = datetime.now().isoformat()
            
            return {"success": True, "message": "Message sent", "size": len(message_text)}
            
        except Exception as e:
            logger.error(f"Error sending message from client '{self.name}': {e}")
            return {"success": False, "error": str(e)}
    
    async def build_connection_url(self) -> str:
        """Build WebSocket connection URL with authentication parameters."""
        try:
            auth_config = self.auth_config
            auth_type = auth_config.get("type", "none")
            
            if auth_type == "query_param":
                # Add authentication token as query parameter
                parsed_url = urlparse(self.url)
                query_params = dict(parse_qsl(parsed_url.query))
                
                param_name = auth_config.get("param_name", "token")
                token_value = auth_config.get("value", auth_config.get("token", ""))
                
                # Evaluate token value with expressions
                context = {"env": dict(os.environ)} if hasattr(os, 'environ') else {}
                evaluated_token = evaluate_expression(token_value, context)
                
                query_params[param_name] = evaluated_token
                
                # Rebuild URL
                new_query = urlencode(query_params)
                connection_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                if new_query:
                    connection_url += f"?{new_query}"
                
                return connection_url
            
            return self.url
            
        except Exception as e:
            logger.error(f"Error building connection URL: {e}")
            return self.url
    
    async def build_connection_headers(self) -> dict:
        """Build WebSocket connection headers with authentication."""
        try:
            headers = {}
            auth_config = self.auth_config
            auth_type = auth_config.get("type", "none")
            
            if auth_type == "bearer_token":
                token_value = auth_config.get("token", "")
                # Evaluate token value with expressions
                context = {"env": dict(os.environ)} if hasattr(os, 'environ') else {}
                evaluated_token = evaluate_expression(token_value, context)
                headers["Authorization"] = f"Bearer {evaluated_token}"
                
            elif auth_type == "header":
                header_name = auth_config.get("header_name", "X-Auth-Token")
                token_value = auth_config.get("value", auth_config.get("token", ""))
                # Evaluate token value with expressions
                context = {"env": dict(os.environ)} if hasattr(os, 'environ') else {}
                evaluated_token = evaluate_expression(token_value, context)
                headers[header_name] = evaluated_token
            
            return headers
            
        except Exception as e:
            logger.error(f"Error building connection headers: {e}")
            return {}
    
    def get_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Get SSL context for secure connections."""
        try:
            if not self.url.startswith("wss://"):
                return None
            
            # Create default SSL context
            ssl_context = ssl.create_default_context()
            
            # Add custom SSL configuration if available
            ssl_config = self.config.get("ssl", {})
            if ssl_config.get("ca_file"):
                ssl_context.load_verify_locations(ssl_config["ca_file"])
            
            return ssl_context
            
        except Exception as e:
            logger.error(f"Error creating SSL context: {e}")
            return None
    
    async def listen_loop(self):
        """Background task for listening to incoming messages."""
        try:
            async for message in self.websocket:
                try:
                    await self.handle_message(message)
                except Exception as e:
                    logger.error(f"Error handling message in client '{self.name}': {e}")
                    logger.error(traceback.format_exc())
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket client '{self.name}' connection closed")
            self.connected = False
            self.last_disconnect_time = datetime.now().isoformat()
            
            # Schedule reconnection if enabled
            if self.auto_reconnect and self.should_reconnect and self.reconnect_attempts < self.max_reconnect_attempts:
                self.schedule_reconnect()
                
        except Exception as e:
            logger.error(f"Listen loop error for client '{self.name}': {e}")
            logger.error(traceback.format_exc())
            self.connected = False
    
    async def handle_message(self, message):
        """Handle incoming message from server."""
        try:
            # Update metrics
            self.metrics["total_messages_received"] += 1
            self.metrics["last_activity"] = datetime.now().isoformat()
            
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
            
            # Execute message handlers
            await self.execute_message_handlers(message_data)
            
        except Exception as e:
            logger.error(f"Error handling message in client '{self.name}': {e}")
            logger.error(traceback.format_exc())
    
    async def execute_message_handlers(self, message_data: dict):
        """Execute pipeline handlers for incoming messages."""
        try:
            handlers = self.message_handlers.get("on_message", [])
            if not handlers:
                return
            
            # Build context for pipeline execution
            context = {
                "websocket": {
                    "timestamp": datetime.now().isoformat(),
                    "connection_type": "client",
                    "connection_name": self.name,
                    "url": self.url,
                    "subprotocol": self.subprotocol,
                    "connected_at": self.last_connect_time,
                    "message": message_data
                },
                "connection": {
                    "total_messages_sent": self.metrics["total_messages_sent"],
                    "total_messages_received": self.metrics["total_messages_received"],
                    "last_activity": self.metrics["last_activity"],
                    "connection_attempts": self.metrics["connection_attempts"]
                }
            }
            
            # Execute handlers
            for handler in handlers:
                try:
                    # Check condition if present
                    condition = handler.get("condition")
                    if condition:
                        condition_result = evaluate_expression(condition, context)
                        if not condition_result:
                            continue
                    
                    # Execute handler
                    if "tool" in handler:
                        await self.execute_single_handler(handler, context)
                    elif "pipeline" in handler:
                        # Full pipeline execution
                        from ...tools.lng_batch_run.tool import run_tool as run_batch_tool
                        
                        pipeline_params = {
                            "pipeline": handler["pipeline"],
                            "context_fields": ["websocket", "connection"]
                        }
                        # Add context variables
                        for key, value in context.items():
                            pipeline_params[f"context_{key}"] = value
                        
                        await run_batch_tool("lng_batch_run", pipeline_params)
                        
                except Exception as e:
                    logger.error(f"Error executing message handler: {e}")
                    logger.error(traceback.format_exc())
        
        except Exception as e:
            logger.error(f"Error in message handler execution: {e}")
            logger.error(traceback.format_exc())
    
    async def execute_single_handler(self, handler: dict, context: dict):
        """Execute a single handler tool."""
        try:
            tool_name = handler.get("tool")
            tool_params = handler.get("params", {})
            
            # Evaluate parameters with context
            evaluated_params = substitute_in_object(tool_params, context)
            
            # Import and execute tool dynamically
            from ...tools.tool_registry import get_tool
            tool_function = get_tool(tool_name)
            
            if tool_function:
                await tool_function(tool_name, evaluated_params)
            else:
                logger.warning(f"Tool '{tool_name}' not found for handler execution")
                
        except Exception as e:
            logger.error(f"Error executing single handler: {e}")
            logger.error(traceback.format_exc())
    
    async def heartbeat_loop(self):
        """Background task for sending heartbeats to server."""
        try:
            heartbeat_interval = self.connection_handling.get("heartbeat_interval", 30)
            
            while self.connected:
                await asyncio.sleep(heartbeat_interval)
                
                if not self.connected or not self.websocket:
                    break
                
                try:
                    # Send heartbeat message
                    if self.heartbeat_message:
                        await self.send_message(self.heartbeat_message)
                    else:
                        # Send WebSocket ping
                        await self.websocket.ping()
                        
                except Exception as e:
                    logger.warning(f"Heartbeat failed for client '{self.name}': {e}")
                    # Connection might be lost, let listen_loop handle reconnection
                    break
                    
        except asyncio.CancelledError:
            logger.info(f"Heartbeat loop cancelled for client '{self.name}'")
        except Exception as e:
            logger.error(f"Heartbeat loop error for client '{self.name}': {e}")
    
    def schedule_reconnect(self):
        """Schedule reconnection attempt."""
        if not self.should_reconnect or self.reconnect_attempts >= self.max_reconnect_attempts:
            return
        
        self.reconnect_attempts += 1
        
        # Calculate backoff delay
        if self.backoff_strategy == "exponential":
            delay = min(2 ** (self.reconnect_attempts - 1), 60)  # Max 60 seconds
        elif self.backoff_strategy == "linear":
            delay = min(self.reconnect_attempts * 5, 60)  # 5, 10, 15... max 60 seconds
        else:  # fixed
            delay = 5
        
        logger.info(f"Scheduling reconnect for client '{self.name}' in {delay} seconds (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
        
        self.reconnect_task = asyncio.create_task(self.reconnect_after_delay(delay))
    
    async def reconnect_after_delay(self, delay: float):
        """Reconnect after specified delay."""
        try:
            await asyncio.sleep(delay)
            
            if self.should_reconnect and not self.connected:
                logger.info(f"Attempting to reconnect client '{self.name}'")
                self.metrics["total_reconnects"] += 1
                await self.connect()
                
        except asyncio.CancelledError:
            logger.info(f"Reconnect task cancelled for client '{self.name}'")
        except Exception as e:
            logger.error(f"Reconnect error for client '{self.name}': {e}")
            
            # Schedule next reconnect if needed
            if self.should_reconnect and self.reconnect_attempts < self.max_reconnect_attempts:
                self.schedule_reconnect()
