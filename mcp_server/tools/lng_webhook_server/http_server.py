"""
HTTP Server module for webhook endpoints using aiohttp.
"""
import asyncio
import json
import logging
import ssl
import os
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
from aiohttp import web, ClientTimeout
from aiohttp.web_request import Request
from aiohttp.web_response import Response

# Import new expression system
from mcp_server.pipeline.expressions import substitute_expressions

logger = logging.getLogger('mcp_server.tools.lng_webhook_server.http_server')

class WebhookHTTPServer:
    """HTTP server for handling webhook requests."""
    
    def __init__(self, config: dict):
        self.config = config
        self.name = config['name']
        self.port = config['port']
        self.path = config['path']
        self.bind_host = config['bind_host']
        self.app = None
        self.runner = None
        self.site = None
        self.request_count = 0
        
        # Thread-based mode for MCP event loop isolation
        self.thread_mode = config.get('thread_mode', False)
        self.server_thread = None
        self.event_loop = None
        self.stop_event = None
        
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Setup dedicated logger for this webhook endpoint."""
        from ...logging_config import setup_instance_logger
        return setup_instance_logger(self.name, 'webhook')
        
        return endpoint_logger
    
    async def start(self) -> dict:
        """Start the HTTP server."""
        try:
            self.logger.info(f"Starting webhook server '{self.name}' on {self.bind_host}:{self.port}{self.path}")
            self.logger.info(f"Thread mode: {self.thread_mode}")
            
            # If thread_mode is enabled, start server in separate thread
            if self.thread_mode:
                return await self._start_in_thread()
            
            # Create aiohttp application
            self.app = web.Application()
            
            # Add webhook route
            self.app.router.add_route('*', self.path, self._handle_webhook)
            
            # Add HTML routes if configured
            html_routes = self.config.get('html_routes', [])
            self.logger.info(f"Configuring {len(html_routes)} HTML routes")
            
            for i, route_config in enumerate(html_routes):
                pattern = route_config.get('pattern', '/html/{template}/{param}')
                template = route_config.get('template', 'no template')
                
                # Create closure to capture route_config for this specific route
                def make_html_handler(config):
                    async def html_handler(request):
                        return await self._handle_html_route(request, config)
                    return html_handler
                
                self.app.router.add_get(pattern, make_html_handler(route_config))
                self.logger.info(f"Added HTML route {i+1}: {pattern} -> {template}")
            
            # Add health check route
            self.app.router.add_get('/health', self._handle_health)
            
            # Create runner
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            # Setup SSL if enabled
            ssl_context = None
            if self.config.get('ssl', {}).get('enabled', False):
                ssl_context = self._create_ssl_context()
            
            # Create site
            self.site = web.TCPSite(
                self.runner, 
                self.bind_host, 
                self.port,
                ssl_context=ssl_context
            )
            
            await self.site.start()
            
            protocol = "https" if ssl_context else "http"
            endpoint_url = f"{protocol}://{self.bind_host}:{self.port}{self.path}"
            
            self.logger.info(f"Webhook server started successfully at {endpoint_url}")
            
            return {
                "server_id": f"server_{self.name}",
                "endpoint_url": endpoint_url,
                "started_at": datetime.now().isoformat(),
                "ssl_enabled": ssl_context is not None,
                "thread_mode": self.thread_mode
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start webhook server: {e}")
            raise
    
    async def stop(self):
        """Stop the HTTP server."""
        try:
            self.logger.info(f"Stopping webhook server '{self.name}'")
            
            # If thread mode, stop the thread
            if self.thread_mode and self.stop_event:
                self.logger.info("Stopping thread-based server")
                # Signal the thread to stop
                if self.event_loop:
                    self.event_loop.call_soon_threadsafe(self.stop_event.set)
                
                # Wait for thread to finish (with timeout)
                if self.server_thread and self.server_thread.is_alive():
                    self.server_thread.join(timeout=5)
                    if self.server_thread.is_alive():
                        self.logger.warning("Server thread did not stop within timeout")
                
                self.logger.info("Thread-based server stopped")
                return
            
            if self.site:
                await self.site.stop()
            
            if self.runner:
                await self.runner.cleanup()
            
            self.logger.info(f"Webhook server '{self.name}' stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping webhook server: {e}")
            raise

    async def _start_in_thread(self) -> dict:
        """Start webhook server in separate thread with own event loop."""
        self.logger.info(f"Starting webhook server in separate thread mode")
        
        # Threading event to signal when server is ready
        server_ready = threading.Event()
        result_holder = {}
        
        def run_server_thread():
            """Run server in dedicated thread with own event loop."""
            try:
                # Create new event loop for this thread
                self.event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.event_loop)
                
                # Create stop event
                self.stop_event = asyncio.Event()
                
                async def start_server():
                    try:
                        # Create aiohttp application
                        self.app = web.Application()
                        
                        # Add webhook route
                        self.app.router.add_route('*', self.path, self._handle_webhook)
                        
                        # Add HTML routes if configured
                        html_routes = self.config.get('html_routes', [])
                        for i, route_config in enumerate(html_routes):
                            pattern = route_config.get('pattern', '/html/{template}/{param}')
                            
                            def make_html_handler(config):
                                async def html_handler(request):
                                    return await self._handle_html_route(request, config)
                                return html_handler
                            
                            self.app.router.add_get(pattern, make_html_handler(route_config))
                        
                        # Add health check route
                        self.app.router.add_get('/health', self._handle_health)
                        
                        # Create runner
                        self.runner = web.AppRunner(self.app)
                        await self.runner.setup()
                        
                        # Setup SSL if enabled
                        ssl_context = None
                        if self.config.get('ssl', {}).get('enabled', False):
                            ssl_context = self._create_ssl_context()
                        
                        # Create site
                        self.site = web.TCPSite(
                            self.runner, 
                            self.bind_host, 
                            self.port,
                            ssl_context=ssl_context
                        )
                        
                        await self.site.start()
                        
                        protocol = "https" if ssl_context else "http"
                        endpoint_url = f"{protocol}://{self.bind_host}:{self.port}{self.path}"
                        
                        result_holder['result'] = {
                            "server_id": f"server_{self.name}",
                            "endpoint_url": endpoint_url,
                            "started_at": datetime.now().isoformat(),
                            "ssl_enabled": ssl_context is not None,
                            "thread_mode": self.thread_mode
                        }
                        
                        self.logger.info(f"Thread-based webhook server started at {endpoint_url}")
                        server_ready.set()
                        
                        # Wait for stop signal
                        await self.stop_event.wait()
                        
                    except Exception as e:
                        self.logger.error(f"Error in thread-based server: {e}")
                        result_holder['error'] = str(e)
                        server_ready.set()
                        
                    finally:
                        # Cleanup
                        if self.site:
                            await self.site.stop()
                        if self.runner:
                            await self.runner.cleanup()
                        self.logger.info(f"Thread-based server cleanup completed")
                
                # Run the server
                self.event_loop.run_until_complete(start_server())
                
            except Exception as e:
                self.logger.error(f"Thread error: {e}")
                result_holder['error'] = str(e)
                server_ready.set()
            finally:
                if self.event_loop:
                    self.event_loop.close()
        
        # Start server thread
        self.server_thread = threading.Thread(target=run_server_thread, daemon=True)
        self.server_thread.start()
        
        # Wait for server to be ready (with timeout)
        if not server_ready.wait(timeout=10):
            raise TimeoutError("Server failed to start within 10 seconds")
        
        if 'error' in result_holder:
            raise RuntimeError(f"Server failed to start: {result_holder['error']}")
        
        return result_holder['result']
    
    
    async def _handle_webhook(self, request: Request) -> Response:
        """Handle incoming webhook requests."""
        self.request_count += 1
        request_id = f"{self.name}-{self.request_count:06d}"
        start_time = datetime.now()
        
        try:
            # Log comprehensive request information
            full_url = f"{request.scheme}://{request.host}{request.path_qs}"
            self.logger.info(f"[{request_id}] Received {request.method} request from {request.remote}")
            self.logger.info(f"[{request_id}] Full URL: {full_url}")
            self.logger.info(f"[{request_id}] Path: {request.path}")
            self.logger.info(f"[{request_id}] Query String: {request.query_string}")
            
            # Parse request data
            webhook_data = await self._parse_request(request, request_id)
            
            # Log request details
            self.logger.info(f"[{request_id}] Headers: {dict(request.headers)}")
            self.logger.info(f"[{request_id}] Content-Type: {webhook_data['content_type']}")
            if webhook_data['body']:
                body_preview = str(webhook_data['body'])[:200] + ("..." if len(str(webhook_data['body'])) > 200 else "")
                self.logger.info(f"[{request_id}] Body preview: {body_preview}")
            self.logger.info(f"[{request_id}] Body size: {len(str(webhook_data['body']))} chars")
            
            # Authenticate request if auth is configured
            auth_result = await self._authenticate_request(request, webhook_data, request_id)
            if not auth_result['success']:
                self.logger.warning(f"[{request_id}] Authentication failed: {auth_result['error']}")
                return web.json_response(
                    {"error": "Authentication failed"},
                    status=401
                )
            
            # Execute pipeline if configured
            pipeline_result = None
            pipeline_success = True
            error_id = None
            
            if self.config.get('pipeline'):
                try:
                    if self.config.get('async_mode', False):
                        # Async mode - respond immediately, process in background
                        asyncio.create_task(self._execute_pipeline_async(webhook_data, request_id))
                        pipeline_result = {"status": "processing_async"}
                    else:
                        # Sync mode - wait for pipeline completion
                        pipeline_result = await self._execute_pipeline(webhook_data, request_id)
                        pipeline_success = pipeline_result.get('success', True)
                        
                except Exception as e:
                    error_id = f"ERR-{request_id}"
                    pipeline_success = False
                    self.logger.error(f"[{request_id}] Pipeline execution failed [{error_id}]: {e}")
                    
                    # Return 500 error with minimal info
                    return web.json_response(
                        {
                            "error": "Internal processing error",
                            "error_id": error_id,
                            "message": "Please contact support with this error ID"
                        },
                        status=500
                    )
            
            # Prepare response context
            execution_time = (datetime.now() - start_time).total_seconds()
            response_context = {
                "webhook": webhook_data,
                "pipeline": {
                    "success": pipeline_success,
                    "execution_time": execution_time,
                    "error_id": error_id
                }
            }
            
            # Add pipeline results to context if available
            if pipeline_result and isinstance(pipeline_result, dict):
                response_context.update(pipeline_result.get('context', {}))
            
            # Check if HTML routes are configured and match current path
            html_routes = self.config.get('response', {}).get('html_routes', [])
            for html_route in html_routes:
                if html_route.get('pattern') == self.path:
                    # This is an HTML route - render HTML template
                    return await self._handle_html_response(
                        html_route, 
                        response_context, 
                        request_id, 
                        execution_time
                    )
            
            # Generate JSON response (default behavior)
            response_config = self.config.get('response', {})
            response_body = self._substitute_variables(
                response_config.get('body', {"received": True}),
                response_context
            )
            
            response_headers = response_config.get('headers', {})
            response_status = response_config.get('status', 200)
            
            # Log detailed response information
            response_body_preview = str(response_body)[:300] + ("..." if len(str(response_body)) > 300 else "")
            
            self.logger.info(f"[{request_id}] 📤 Responding with status {response_status} after {execution_time:.3f}s")
            self.logger.info(f"[{request_id}] 📤 Response headers: {response_headers}")
            self.logger.info(f"[{request_id}] 📤 Response body preview: {response_body_preview}")
            self.logger.info(f"[{request_id}] 📤 Response size: {len(str(response_body))} chars")
            
            # Check if Content-Type is in headers to avoid aiohttp conflict
            content_type = response_headers.pop('Content-Type', 'application/json')
            
            return web.json_response(
                response_body,
                status=response_status,
                headers=response_headers,
                content_type=content_type
            )
            
        except Exception as e:
            error_id = f"ERR-{request_id}"
            self.logger.error(f"[{request_id}] Unexpected error [{error_id}]: {e}")
            
            return web.json_response(
                {
                    "error": "Internal server error",
                    "error_id": error_id
                },
                status=500
            )
    
    async def _handle_html_route(self, request: Request, route_config: dict) -> Response:
        """Handle HTML route requests."""
        request_id = f"{self.name}-html-{self.request_count:06d}"
        self.request_count += 1
        start_time = datetime.now()
        
        try:
            # Get URL parameters
            url_params = request.match_info
            query_params = dict(request.query)
            
            self.logger.info(f"[{request_id}] HTML request: {request.path}")
            self.logger.info(f"[{request_id}] URL params: {url_params}")
            self.logger.info(f"[{request_id}] Query params: {query_params}")
            self.logger.info(f"[{request_id}] Route config: {route_config}")
            
            # Prepare context for template and pipeline
            context = {
                "url": url_params,
                "query": query_params,
                "request": {
                    "path": request.path,
                    "method": request.method,
                    "headers": dict(request.headers),
                    "remote_ip": request.remote
                },
                "env": dict(os.environ),
                "webhook": {
                    "name": self.name,
                    "bind_host": self.bind_host,
                    "port": self.port,
                    "path": self.path,
                    "endpoint": f"http://{self.bind_host}:{self.port}{self.path}"
                }
            }
            
            # Execute pipeline if configured
            if route_config.get('pipeline'):
                try:
                    pipeline_result = await self._execute_html_pipeline(
                        route_config['pipeline'], 
                        context, 
                        request_id
                    )
                    
                    # Add pipeline results to context
                    if isinstance(pipeline_result, dict) and 'context' in pipeline_result:
                        context.update(pipeline_result['context'])
                        
                except Exception as e:
                    self.logger.error(f"[{request_id}] HTML pipeline failed: {e}")
                    return web.Response(
                        text=f"Pipeline execution failed: {str(e)}",
                        status=500,
                        content_type='text/plain'
                    )
            
            # Process custom mapping if configured
            if route_config.get('mapping'):
                try:
                    custom_mapping = await self._process_custom_mapping(
                        route_config['mapping'], 
                        context, 
                        request_id
                    )
                    
                    # Add custom mapping results to context  
                    context.update(custom_mapping)
                    self.logger.info(f"[{request_id}] Custom mapping processed: {len(custom_mapping)} variables")
                    
                except Exception as e:
                    self.logger.error(f"[{request_id}] Custom mapping failed: {e}")
                    return web.Response(
                        text=f"Mapping processing failed: {str(e)}",
                        status=500,
                        content_type='text/plain'
                    )
            
            # Load and process HTML template
            template_path = route_config.get('template')
            if not template_path:
                return web.Response(
                    text="Template path not configured",
                    status=500,
                    content_type='text/plain'
                )
            
            # Substitute variables in template path
            template_path = self._substitute_variables(template_path, context)
            
            try:
                html_content = await self._load_and_process_template(template_path, context)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                self.logger.info(f"[{request_id}] ✅ HTML response generated in {execution_time:.3f}s")
                
                return web.Response(
                    text=html_content,
                    status=200,
                    content_type='text/html',
                    charset='utf-8'
                )
                
            except FileNotFoundError:
                self.logger.error(f"[{request_id}] Template not found: {template_path}")
                return web.Response(
                    text=f"Template not found: {template_path}",
                    status=404,
                    content_type='text/plain'
                )
            except Exception as e:
                self.logger.error(f"[{request_id}] Template processing failed: {e}")
                return web.Response(
                    text=f"Template processing failed: {str(e)}",
                    status=500,
                    content_type='text/plain'
                )
                
        except Exception as e:
            self.logger.error(f"[{request_id}] HTML route error: {e}")
            return web.Response(
                text=f"Internal server error: {str(e)}",
                status=500,
                content_type='text/plain'
            )
    
    async def _handle_html_response(self, html_route: dict, context: dict, request_id: str, execution_time: float) -> Response:
        """Handle HTML response for webhook endpoint."""
        try:
            self.logger.info(f"[{request_id}] 🎨 Generating HTML response using template")
            
            # Process custom mapping if configured
            if html_route.get('mapping'):
                try:
                    custom_mapping = await self._process_custom_mapping(
                        html_route['mapping'], 
                        context, 
                        request_id
                    )
                    
                    # Add custom mapping results to context  
                    context.update(custom_mapping)
                    self.logger.info(f"[{request_id}] Custom mapping processed: {len(custom_mapping)} variables")
                    
                except Exception as e:
                    self.logger.error(f"[{request_id}] Custom mapping failed: {e}")
                    return web.Response(
                        text=f"Mapping processing failed: {str(e)}",
                        status=500,
                        content_type='text/plain'
                    )
            
            # Load and process HTML template
            template_path = html_route.get('template')
            if not template_path:
                return web.Response(
                    text="Template path not configured",
                    status=500,
                    content_type='text/plain'
                )
            
            # Substitute variables in template path
            template_path = self._substitute_variables(template_path, context)
            
            try:
                html_content = await self._load_and_process_template(template_path, context)
                
                self.logger.info(f"[{request_id}] ✅ HTML response generated in {execution_time:.3f}s")
                self.logger.info(f"[{request_id}] 📤 HTML response size: {len(html_content)} chars")
                
                return web.Response(
                    text=html_content,
                    status=200,
                    content_type='text/html',
                    charset='utf-8'
                )
                
            except FileNotFoundError:
                self.logger.error(f"[{request_id}] Template not found: {template_path}")
                return web.Response(
                    text=f"Template not found: {template_path}",
                    status=404,
                    content_type='text/plain'
                )
            except Exception as e:
                self.logger.error(f"[{request_id}] Template processing failed: {e}")
                return web.Response(
                    text=f"Template processing failed: {str(e)}",
                    status=500,
                    content_type='text/plain'
                )
                
        except Exception as e:
            self.logger.error(f"[{request_id}] HTML response error: {e}")
            return web.Response(
                text=f"Internal server error: {str(e)}",
                status=500,
                content_type='text/plain'
            )
    
    async def _execute_html_pipeline(self, pipeline_steps: list, context: dict, request_id: str) -> dict:
        """Execute pipeline for HTML route."""
        try:
            self.logger.info(f"[{request_id}] ⚙️ Starting HTML pipeline with {len(pipeline_steps)} steps")
            
            # Substitute variables in pipeline steps
            substituted_steps = self._substitute_variables(pipeline_steps, context)
            
            # Import here to avoid circular imports
            from mcp_server.tools.lng_batch_run.tool import run_tool as run_batch_pipeline
            
            # Execute using lng_batch_run
            pipeline_params = {
                "pipeline": substituted_steps,
                "final_result": "HTML pipeline completed",
                "context_fields": ["*"]
            }
            
            result_content = await run_batch_pipeline("lng_batch_run", pipeline_params)
            
            if result_content and len(result_content) > 0:
                result_data = json.loads(result_content[0].text)
                self.logger.info(f"[{request_id}] ✅ HTML pipeline completed successfully")
                return result_data
            else:
                return {"success": False, "error": "Empty pipeline result"}
                
        except Exception as e:
            self.logger.error(f"[{request_id}] HTML pipeline execution failed: {e}")
            raise
    
    async def _load_and_process_template(self, template_path: str, context: dict) -> str:
        """Load HTML template and substitute placeholders."""
        
        # Read template file
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Simple placeholder substitution using {{VARIABLE}} format
        processed_content = template_content
        
        # Replace placeholders using context (which should already contain processed variables)
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                placeholder = "{{" + str(key).upper() + "}}"
                if placeholder in processed_content:
                    processed_content = processed_content.replace(placeholder, str(value))
        
        return processed_content

    async def _process_custom_mapping(self, mapping: dict, context: dict, request_id: str) -> dict:
        """Process custom mapping expressions to create template variables."""
        try:
            from ...pipeline.expressions import evaluate_expression
            
            custom_vars = {}
            
            for placeholder_name, expression in mapping.items():
                try:
                    # Evaluate the expression using the context
                    result = evaluate_expression(expression, context, expected_result_type="python")
                    custom_vars[placeholder_name.upper()] = str(result) if result is not None else ""
                    
                    self.logger.debug(f"[{request_id}] Mapping: {placeholder_name} = {expression} -> {result}")
                    
                except Exception as e:
                    self.logger.warning(f"[{request_id}] Failed to evaluate mapping '{placeholder_name}': {expression} - {e}")
                    # Set empty value on evaluation failure
                    custom_vars[placeholder_name.upper()] = ""
            
            return custom_vars
            
        except Exception as e:
            self.logger.error(f"[{request_id}] Custom mapping processing error: {e}")
            return {}

    async def _handle_health(self, request: Request) -> Response:
        """Health check endpoint."""
        return web.json_response({
            "status": "healthy",
            "webhook_name": self.name,
            "requests_processed": self.request_count,
            "uptime": (datetime.now() - datetime.fromisoformat(
                self.config.get('created_at', datetime.now().isoformat())
            )).total_seconds()
        })
    
    async def _parse_request(self, request: Request, request_id: str) -> dict:
        """Parse incoming request into webhook data structure."""
        content_type = request.headers.get('content-type', '').lower()
        
        # Parse body based on content type
        body = {}
        if 'application/json' in content_type:
            try:
                body = await request.json()
            except Exception as e:
                self.logger.warning(f"[{request_id}] Failed to parse JSON body: {e}")
                body = {"error": "Invalid JSON", "raw": await request.text()}
        elif 'application/x-www-form-urlencoded' in content_type:
            try:
                form_data = await request.post()
                body = dict(form_data)
            except Exception as e:
                self.logger.warning(f"[{request_id}] Failed to parse form data: {e}")
                body = {"error": "Invalid form data", "raw": await request.text()}
        else:
            # Plain text or other
            body = {"text": await request.text()}
        
        # Build webhook data structure
        webhook_data = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "path": str(request.url.path),
            "query": dict(request.url.query),
            "headers": dict(request.headers),
            "body": body,
            "remote_ip": request.remote,
            "content_type": content_type,
            "endpoint_name": self.name,
            "request_id": request_id
        }
        
        return webhook_data
    
    async def _authenticate_request(self, request: Request, webhook_data: dict, request_id: str) -> dict:
        """Authenticate incoming request based on configuration."""
        auth_config = self.config.get('auth', {})
        auth_type = auth_config.get('type', 'none')
        
        if auth_type == 'none':
            return {"success": True}
        
        # Implementation for different auth types will be added later
        self.logger.info(f"[{request_id}] Authentication type '{auth_type}' - implementation pending")
        return {"success": True}  # Temporary - allow all
    
    async def _execute_pipeline(self, webhook_data: dict, request_id: str) -> dict:
        """Execute pipeline synchronously."""
        try:
            pipeline_steps = self.config['pipeline']
            self.logger.info(f"[{request_id}] ⚙️ Starting pipeline execution with {len(pipeline_steps)} steps")
            
            # Prepare initial context with webhook data
            initial_context = {
                "webhook": webhook_data
            }
            
            # Substitute variables in pipeline steps
            substituted_steps = self._substitute_variables(pipeline_steps, initial_context)
            
            # Log pipeline steps (with substituted values)
            for i, step in enumerate(substituted_steps, 1):
                tool_name = step.get('tool', 'unknown')
                params_preview = str(step.get('params', {}))[:100] + ("..." if len(str(step.get('params', {}))) > 100 else "")
                output_var = step.get('output', 'none')
                self.logger.info(f"[{request_id}] ⚙️ Step {i}/{len(substituted_steps)}: {tool_name} → {output_var} | params: {params_preview}")
            
            # Import here to avoid circular imports
            from mcp_server.tools.lng_batch_run.tool import run_tool as run_batch_pipeline
            
            # Prepare pipeline parameters
            pipeline_params = {
                "pipeline": substituted_steps,
                "final_result": "Pipeline completed",
                "context_fields": ["*"]  # Show all context variables
            }
            
            # Execute using lng_batch_run
            result_content = await run_batch_pipeline("lng_batch_run", pipeline_params)
            
            # Debug: Log raw result
            self.logger.info(f"[{request_id}] 🔍 Raw pipeline result: {result_content}")
            self.logger.info(f"[{request_id}] 🔍 Result type: {type(result_content)}")
            
            # Parse result
            if result_content and len(result_content) > 0:
                result_text = result_content[0].text
                self.logger.info(f"[{request_id}] 🔍 Result text: {result_text[:500]}...")
                result_data = json.loads(result_text)
                self.logger.info(f"[{request_id}] 🔍 Parsed result data: {result_data}")
                
                # Log pipeline results
                if 'context' in result_data:
                    context_keys = list(result_data['context'].keys())
                    self.logger.info(f"[{request_id}] ⚙️ Pipeline output variables: {context_keys}")
                    
                    # Log each output variable (truncated)
                    for key, value in result_data['context'].items():
                        value_preview = str(value)[:150] + ("..." if len(str(value)) > 150 else "")
                        self.logger.info(f"[{request_id}] ⚙️ Variable '{key}': {value_preview}")
                else:
                    self.logger.warning(f"[{request_id}] ⚠️ No 'context' key in result_data")
                
                self.logger.info(f"[{request_id}] ✅ Pipeline completed successfully")
                return result_data
            else:
                self.logger.warning(f"[{request_id}] Pipeline returned empty result")
                return {"success": False, "error": "Empty pipeline result"}
                
        except Exception as e:
            self.logger.error(f"[{request_id}] Pipeline execution failed: {e}")
            raise
    
    async def _execute_pipeline_async(self, webhook_data: dict, request_id: str):
        """Execute pipeline asynchronously (fire and forget)."""
        try:
            result = await self._execute_pipeline(webhook_data, request_id)
            self.logger.info(f"[{request_id}] Async pipeline completed: {result.get('success', False)}")
        except Exception as e:
            self.logger.error(f"[{request_id}] Async pipeline failed: {e}")
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for HTTPS."""
        ssl_config = self.config.get('ssl', {})
        
        if ssl_config.get('cert_file') and ssl_config.get('key_file'):
            # User-provided certificates
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(ssl_config['cert_file'], ssl_config['key_file'])
            self.logger.info("Using user-provided SSL certificates")
        else:
            # Self-signed certificate (for development)
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            # Note: Self-signed cert generation would need additional implementation
            self.logger.warning("Self-signed SSL certificate generation not yet implemented")
            raise NotImplementedError("Self-signed SSL certificates not yet supported")
        
        return context
    
    def _substitute_variables(self, obj: Any, context: dict) -> Any:
        """Substitute variables in response template using new expression system."""
        if isinstance(obj, dict):
            return {k: self._substitute_variables(v, context) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_variables(item, context) for item in obj]
        elif isinstance(obj, str) and ("{!" in obj or "[!" in obj):
            try:
                return substitute_expressions(obj, context, expected_result_type="python")
            except Exception as e:
                logger.warning(f"Variable substitution failed for '{obj}': {e}")
                return obj
        else:
            return obj
