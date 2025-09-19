import mcp.types as types
import json
import logging
import asyncio
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger('mcp_server.tools.lng_webhook_server')

# Global storage for active webhook servers
ACTIVE_WEBHOOKS: Dict[str, Dict] = {}

# Flag to track if webhooks have been restored
_webhooks_restored = False

async def tool_info() -> dict:
    return {
        "description": """Universal webhook server constructor with pipeline integration.

**Universal Webhook Constructor**
Create HTTP endpoints that receive webhooks and execute pipelines automatically.

**Operations:**
• `start` - Create new webhook endpoint with full configuration
• `stop` - Stop webhook endpoint by name
• `list` - List all active webhook endpoints
• `status` - Get detailed status of specific endpoint
• `test` - Manual test webhook with mock data
• `update` - Update pipeline configuration without restart

**Features:**
**Pipeline Integration** - Auto-execute lng_batch_run pipelines
**Authentication** - GitHub signatures, Bearer tokens, Basic auth
**Detailed Logging** - Structured logs per endpoint with error tracking
**High Performance** - Async processing with request queuing
**SSL Support** - HTTPS with custom or self-signed certificates
**Persistence** - Auto-restore webhooks on server restart
**File-Based Configuration** - Use `config_file` parameter to load webhook config from JSON files
**Persistent Mode** - Run webhook server in background task for MCP HTTP Client compatibility
**Thread Mode** - Run webhook server in separate thread with isolated event loop (solves MCP deadlock)

**Configuration Loading:**
1. **Inline Configuration**: Pass all parameters directly in the tool call
2. **File-Based Configuration**: Use `config_file` parameter to load config from JSON file
3. **Parameter Override**: Can combine file config with direct parameters (direct params take priority)

**Example Inline Configuration:**
```json
{
  "operation": "start",
  "name": "github-ci",
  "port": 8080,
  "path": "/github",
  "bind_host": "0.0.0.0",
  "async_mode": false,
  "thread_mode": true,
  "timeout": 30,
  "auth": {
    "type": "github_signature",
    "secret": "webhook-secret"
  },
  "ssl": {
    "enabled": true,
    "cert_file": "path/to/cert.pem",
    "key_file": "path/to/key.pem"
  },
  "response": {
    "status": 200,
    "headers": {"Content-Type": "application/json"},
    "body": {
      "received": true,
      "processed": "{! pipeline.success !}",
      "commit_count": "{! webhook.body.commits.length !}"
    }
  },
  "html_routes": [
    {
      "pattern": "/html/{template}/{param}",
      "template": "mcp_server/tools/{template}/status.html",
      "mapping": {
        "URL_TEMPLATE": "{! url.template !}",
        "URL_PARAM": "{! url.param !}",
        "FORMATTED_PARAM": "{! 'Parameter: ' + url.param !}",
        "PARAM_UPPER": "{! url.param.toUpperCase() !}",
        "CURRENT_TIME": "{! new Date().toISOString() !}",
        "PAGE_DATA_COUNT": "{! page_data.wordCount || 0 !}"
      },
      "pipeline": [
        {
          "tool": "{template}",
          "params": {
            "operation": "session_status",
            "session_id": "{! url.param !}"
          },
          "output": "page_data"
        }
      ]
    },
    {
      "pattern": "/cookies/{sessionId}",
      "template": "mcp_server/tools/lng_cookie_grabber/status.html",
      "mapping": {
        "URL_SESSIONID": "{! url.sessionId !}",
        "SESSION_DISPLAY": "{! 'Session ID: ' + url.sessionId !}",
        "SESSION_LENGTH": "[! len(url.sessionId) !]",
        "IS_VALID_SESSION": "{! url.sessionId.length > 5 !}"
      }
    }
  ],
  "pipeline": [
    {
      "tool": "lng_count_words",
      "params": {"input_text": "{! webhook.body.commits[0].message !}"},
      "output": "stats"
    }
  ]
}
```

**Example File-Based Configuration:**

Create a JSON file (e.g., `webhook_config.json`):
```json
{
  "name": "cookie-status-server",
  "port": 9000,
  "path": "/api",
  "bind_host": "localhost",
  "html_routes": [
    {
      "pattern": "/cookies/{sessionId}",
      "template": "mcp_server/tools/lng_cookie_grabber/status.html",
      "mapping": {
        "SESSION_ID": "{! url.sessionId !}",
        "FORMATTED_SESSION": "{! 'Session: ' + url.sessionId !}"
      }
    }
  ],
  "response": {
    "status": 200,
    "headers": {"Content-Type": "application/json"},
    "body": {"message": "Cookie status server is running"}
  }
}
```

Then use it:
```json
{
  "operation": "start",
  "config_file": "mcp_server/tools/lng_cookie_grabber/webhook.json"
}
```

**Parameter Merging:**
When using `config_file`, you can still override specific parameters:
```json
{
  "operation": "start",
  "config_file": "webhook_config.json",
  "port": 9001,
  "bind_host": "0.0.0.0"
}
```

**Benefits of File-Based Configuration:**
- **Reusability**: Share webhook configs across different deployments
- **Version Control**: Track webhook configuration changes in git
- **Organization**: Keep complex webhook configs in separate files  
- **Maintenance**: Easier to edit and debug large configurations
- **Parameter Override**: Can still override specific parameters when needed

**Webhook Context Available in Pipeline:**
```json
{
  "webhook": {
    "timestamp": "2025-08-03T13:45:30.123Z",
    "method": "POST",
    "path": "/github",
    "headers": {"user-agent": "GitHub-Hookshot/...", ...},
    "query": {"ref": "main"},
    "body": {"action": "push", "commits": [...]},
    "remote_ip": "192.30.252.0",
    "content_type": "application/json",
    "signature": "sha256=...",
    "endpoint_name": "github-ci"
  },
  "pipeline": {
    "execution_time": 0.234,
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
                    "enum": ["start", "stop", "list", "status", "test", "update"]
                },
                "name": {
                    "type": "string",
                    "description": "Unique name for the webhook endpoint"
                },
                "port": {
                    "type": "integer",
                    "description": "Port number for webhook server (1000-65535)",
                    "minimum": 1000,
                    "maximum": 65535
                },
                "path": {
                    "type": "string",
                    "description": "URL path for webhook endpoint (e.g., '/github')"
                },
                "bind_host": {
                    "type": "string",
                    "description": "Host to bind to ('localhost' or '0.0.0.0')"
                },
                "async_mode": {
                    "type": "boolean",
                    "description": "Whether to respond immediately and process pipeline async"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Pipeline execution timeout in seconds"
                },
                "auth": {
                    "type": "object",
                    "description": "Authentication configuration"
                },
                "ssl": {
                    "type": "object",
                    "description": "SSL/HTTPS configuration"
                },
                "response": {
                    "type": "object",
                    "description": "Custom response configuration"
                },
                "pipeline": {
                    "type": "array",
                    "description": "Pipeline steps to execute on webhook",
                    "items": {"type": "object"}
                },
                "test_data": {
                    "type": "object",
                    "description": "Mock data for test operation"
                },
                "html_routes": {
                    "type": "array",
                    "description": "HTML route configurations for serving web pages",
                    "items": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "URL pattern like '/html/{template}/{param}'"
                            },
                            "template": {
                                "type": "string", 
                                "description": "Path to HTML template file"
                            },
                            "pipeline": {
                                "type": "array",
                                "description": "Pipeline to execute for data preparation",
                                "items": {"type": "object"}
                            },
                            "mapping": {
                                "type": "object",
                                "description": "Custom mapping of template placeholders to expressions. Keys are placeholder names (e.g., 'URL_SESSIONID'), values are expressions (e.g., '{! url.sessionId !}' or '[! url.sessionId.upper() !]')",
                                "additionalProperties": {
                                    "type": "string",
                                    "description": "Expression that will be evaluated to provide the placeholder value"
                                }
                            }
                        }
                    }
                },
                "config_file": {
                    "type": "string",
                    "description": "Path to JSON file containing webhook configuration (alternative to inline config)"
                }
            },
            "required": ["operation"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Execute webhook server operations."""
    
    global _webhooks_restored
    
    # Restore webhooks on first use if not done during init
    if not _webhooks_restored:
        await _ensure_webhooks_restored()
    
    try:
        operation = parameters.get("operation")
        
        if operation == "start":
            return await start_webhook(parameters)
        elif operation == "stop":
            return await stop_webhook(parameters)
        elif operation == "list":
            return await list_webhooks()
        elif operation == "status":
            return await webhook_status(parameters)
        elif operation == "test":
            return await test_webhook(parameters)
        elif operation == "update":
            return await update_webhook(parameters)
        else:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }, indent=2)
            )]
            
    except Exception as e:
        logger.error(f"Error in lng_webhook_server: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def start_webhook(params: dict) -> list[types.Content]:
    """Start a new webhook endpoint."""
    try:
        # Store original params to detect config source
        original_params = params.copy()
        
        # Check if config_file is provided and load configuration
        if "config_file" in params:
            config_file = params["config_file"]
            logger.info(f"Loading webhook configuration from file: {config_file}")
            
            try:
                import os
                # Read configuration from file
                if not os.path.isabs(config_file):
                    # Make relative paths relative to the project root
                    import mcp_server
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
                logger.info(f"Successfully loaded webhook configuration from {config_file}")
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
        webhook_name = params.get("name")
        port = params.get("port")
        path = params.get("path", "/webhook")
        
        if not webhook_name:
            raise ValueError("'name' parameter is required")
        if not port:
            raise ValueError("'port' parameter is required")
        
        # Validate port range
        if not (1000 <= port <= 65535):
            raise ValueError("Port must be between 1000 and 65535")
        
        # Stop existing webhook with same name
        if webhook_name in ACTIVE_WEBHOOKS:
            await _stop_webhook_by_name(webhook_name)
            logger.info(f"Stopped existing webhook '{webhook_name}' for restart")
        
        # Create webhook configuration
        config = {
            "name": webhook_name,
            "port": port,
            "path": path,
            "bind_host": params.get("bind_host", "localhost"),
            "async_mode": params.get("async_mode", False),
            "thread_mode": params.get("thread_mode", False),
            "timeout": params.get("timeout", 30),
            "auth": params.get("auth", {"type": "none"}),
            "ssl": params.get("ssl", {"enabled": False}),
            "response": params.get("response", {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": {"received": True}
            }),
            "pipeline": params.get("pipeline", []),
            "html_routes": params.get("html_routes", []),  # Add HTML routes support
            "created_at": datetime.now().isoformat(),
            "status": "starting"
        }
        
        # Save configuration to file
        await _save_webhook_config(webhook_name, config)
        
        # Start HTTP server (will implement in next step)
        server_info = await _start_http_server(config)
        
        # Update status and store server info (not server instance)
        config["status"] = "running"
        config["server_info"] = server_info
        
        # Store server instance in memory only (not in config for JSON)
        ACTIVE_WEBHOOKS[webhook_name] = config
        
        # Save updated config without server instance
        await _save_webhook_config(webhook_name, config)
        
        logger.info(f"Webhook '{webhook_name}' started on {config['bind_host']}:{port}{path}")
        
        # Log HTML routes if any
        html_routes = config.get('html_routes', [])
        if html_routes:
            logger.info(f"Webhook '{webhook_name}' configured with {len(html_routes)} HTML routes:")
            for i, route in enumerate(html_routes):
                pattern = route.get('pattern', 'no pattern')
                template = route.get('template', 'no template')
                pipeline_steps = len(route.get('pipeline', []))
                logger.info(f"  Route {i+1}: {pattern} -> {template} (pipeline: {pipeline_steps} steps)")
        else:
            logger.info(f"Webhook '{webhook_name}' has no HTML routes configured")
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "message": f"Webhook '{webhook_name}' started successfully",
                "endpoint": f"http://{config['bind_host']}:{port}{path}",
                "config": _mask_sensitive_data(config),
                "config_source": "config_file" if "config_file" in original_params else "inline"
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to start webhook: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def stop_webhook(params: dict) -> list[types.Content]:
    """Stop a webhook endpoint."""
    try:
        webhook_name = params.get("name")
        if not webhook_name:
            raise ValueError("'name' parameter is required")
        
        if webhook_name not in ACTIVE_WEBHOOKS:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Webhook '{webhook_name}' not found"
                }, indent=2)
            )]
        
        await _stop_webhook_by_name(webhook_name)
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "message": f"Webhook '{webhook_name}' stopped successfully"
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to stop webhook: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def list_webhooks() -> list[types.Content]:
    """List all active webhooks."""
    try:
        webhooks = []
        for name, config in ACTIVE_WEBHOOKS.items():
            webhooks.append({
                "name": name,
                "port": config["port"],
                "path": config["path"],
                "status": config["status"],
                "created_at": config["created_at"],
                "endpoint": f"http://{config['bind_host']}:{config['port']}{config['path']}",
                "pipeline_steps": len(config.get("pipeline", [])),
                "auth_type": config.get("auth", {}).get("type", "none")
            })
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "active_webhooks": len(webhooks),
                "webhooks": webhooks
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to list webhooks: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def webhook_status(params: dict) -> list[types.Content]:
    """Get detailed status of a webhook."""
    # Implementation placeholder
    return [types.TextContent(
        type="text",
        text=json.dumps({"success": True, "message": "Status operation - to be implemented"}, indent=2)
    )]

async def test_webhook(params: dict) -> list[types.Content]:
    """Test webhook with mock data."""
    import aiohttp
    
    name = params.get("name")
    test_data = params.get("test_data", {})
    
    if not name:
        return [types.TextContent(
            type="text",
            text=json.dumps({"success": False, "error": "Webhook name is required"}, indent=2)
        )]
    
    if name not in ACTIVE_WEBHOOKS:
        return [types.TextContent(
            type="text",
            text=json.dumps({"success": False, "error": f"Webhook '{name}' not found"}, indent=2)
        )]
    
    webhook_config = ACTIVE_WEBHOOKS[name]
    endpoint_url = webhook_config.get("server_info", {}).get("endpoint_url")
    
    if not endpoint_url:
        return [types.TextContent(
            type="text",
            text=json.dumps({"success": False, "error": f"Webhook '{name}' endpoint not available"}, indent=2)
        )]
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint_url,
                json=test_data,
                headers={"Content-Type": "application/json", "User-Agent": "lng_webhook_server/test"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response_text = await response.text()
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": f"Test request sent to '{name}'",
                        "endpoint": endpoint_url,
                        "test_data": test_data,
                        "response": {
                            "status": response.status,
                            "headers": dict(response.headers),
                            "body": response_text
                        }
                    }, indent=2)
                )]
                
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": f"Failed to test webhook '{name}': {str(e)}",
                "endpoint": endpoint_url,
                "test_data": test_data
            }, indent=2)
        )]

async def update_webhook(params: dict) -> list[types.Content]:
    """Update webhook configuration."""
    # Implementation placeholder
    return [types.TextContent(
        type="text",
        text=json.dumps({"success": True, "message": "Update operation - to be implemented"}, indent=2)
    )]

# Helper functions

async def _save_webhook_config(name: str, config: dict):
    """Save webhook configuration to file."""
    import os
    config_dir = "mcp_server/config/webhook"
    os.makedirs(config_dir, exist_ok=True)
    
    # Create a clean config copy without server instance
    clean_config = {k: v for k, v in config.items() if k != '_server_instance'}
    
    config_file = os.path.join(config_dir, f"{name}.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(clean_config, f, indent=2, ensure_ascii=False)

async def _start_http_server(config: dict) -> dict:
    """Start HTTP server for webhook."""
    try:
        from .http_server import WebhookHTTPServer
        
        # Create and start HTTP server
        server = WebhookHTTPServer(config)
        server_info = await server.start()
        
        # Store server instance for later cleanup
        config['_server_instance'] = server
        
        return server_info
        
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {e}")
        raise

async def _stop_webhook_by_name(name: str):
    """Stop webhook by name."""
    if name in ACTIVE_WEBHOOKS:
        config = ACTIVE_WEBHOOKS[name]
        
        # Stop HTTP server if it exists
        server_instance = config.get('_server_instance')
        if server_instance:
            try:
                await server_instance.stop()
            except Exception as e:
                logger.error(f"Error stopping HTTP server for '{name}': {e}")
        
        # Remove from active webhooks
        del ACTIVE_WEBHOOKS[name]
        
        # Remove config file
        config_file = f"mcp_server/config/webhook/{name}.json"
        if os.path.exists(config_file):
            os.remove(config_file)
            
        logger.info(f"Webhook '{name}' stopped and cleaned up")

def _mask_sensitive_data(config: dict) -> dict:
    """Mask sensitive data in configuration."""
    masked = config.copy()
    
    # Remove server instance from output
    if '_server_instance' in masked:
        del masked['_server_instance']
    
    # Mask auth secrets
    if "auth" in masked and "secret" in masked["auth"]:
        secret = masked["auth"]["secret"]
        if len(secret) > 6:
            masked["auth"]["secret"] = secret[:3] + "***" + secret[-3:]
        else:
            masked["auth"]["secret"] = "***"
    
    # Mask SSL key paths
    if "ssl" in masked and "key_file" in masked["ssl"]:
        masked["ssl"]["key_file"] = "***masked***"
    
    return masked

# Auto-restore webhooks on module import
def init():
    """Initialize webhook server - restore webhooks from saved configurations."""
    import asyncio
    
    logger.info("Initializing webhook server - restoring saved configurations")
    
    try:
        config_dir = "mcp_server/config/webhook"
        if not os.path.exists(config_dir):
            logger.info("No webhooks directory found, skipping restoration")
            return
        
        config_files = [f for f in os.listdir(config_dir) if f.endswith('.json')]
        if not config_files:
            logger.info("No webhook configurations found to restore")
            return
        
        logger.info(f"Found {len(config_files)} webhook configurations to restore")
        
        # Try to get current event loop, if none exists, schedule for later
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, schedule the task
            loop.create_task(_restore_webhooks_async())
            logger.info("Webhook restoration scheduled in existing event loop")
        except RuntimeError:
            # No event loop running, we'll restore webhooks when first tool is called
            logger.info("No event loop available at init, webhooks will restore on first use")
        
    except Exception as e:
        logger.error(f"Error in webhook init: {e}")

async def _ensure_webhooks_restored():
    """Ensure webhooks are restored - called on first tool use if not restored during init."""
    global _webhooks_restored
    
    if _webhooks_restored:
        return
    
    logger.info("Restoring webhooks on first tool use")
    await _restore_webhooks_async()
    _webhooks_restored = True

async def _restore_webhooks_async():
    """Restore webhooks asynchronously."""
    try:
        config_dir = "mcp_server/config/webhook"
        
        for filename in os.listdir(config_dir):
            if filename.endswith('.json'):
                name = filename[:-5]  # Remove .json extension
                try:
                    config_file = os.path.join(config_dir, filename)
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    logger.info(f"Restoring webhook '{name}' from saved configuration")
                    
                    # Start HTTP server with saved config
                    config["status"] = "restoring"
                    server_info = await _start_http_server(config)
                    config["status"] = "running"
                    config["server_info"] = server_info
                    
                    # Store in active webhooks
                    ACTIVE_WEBHOOKS[name] = config
                    
                    logger.info(f"Successfully restored webhook '{name}' at {server_info.get('endpoint_url')}")
                    
                except Exception as e:
                    logger.error(f"Failed to restore webhook '{name}': {e}")
                    # Remove failed config file
                    try:
                        os.remove(os.path.join(config_dir, filename))
                    except:
                        pass
                    
    except Exception as e:
        logger.error(f"Failed to restore webhooks: {e}")
    finally:
        global _webhooks_restored
        _webhooks_restored = True
        logger.info("Webhook restoration completed")

# Initialize restoration (will be called by the server)
# asyncio.create_task(_restore_webhooks_on_startup())
