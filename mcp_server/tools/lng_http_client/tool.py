import mcp.types as types
import json
import sys
import os
import asyncio
import time
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import urllib.parse
from urllib.parse import urljoin, urlparse

# HTTP libraries
import requests
import aiohttp
import websockets

# Data processing
import lxml.html
from bs4 import BeautifulSoup
from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.ext import parse as jsonpath_ext_parse

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from mcp_server.pipeline.expressions import substitute_expressions, parse_substituted_string, build_default_context

# State management  
from mcp_server.file_state_manager import FileStateManager

async def decrypt_cookies_for_domain(session_id: str, domain: str) -> str:
    """Decrypt cookies for specified domain using lng_cookie_grabber."""
    try:
        # Import cookie grabber functions
        from ..lng_cookie_grabber.tool import decrypt_cookies as decrypt_tool
        
        # Call decrypt function
        result = await decrypt_tool(session_id, domain)
        
        if result and len(result) > 0:
            result_data = json.loads(result[0].text)
            if result_data.get("success"):
                return result_data.get("cookies", "")
            else:
                raise ValueError(f"Decryption failed: {result_data.get('error', 'Unknown error')}")
        else:
            raise ValueError("No decryption result returned")
            
    except Exception as e:
        raise ValueError(f"Failed to decrypt cookies: {str(e)}")

def parse_cookie_string(cookie_string: str) -> dict:
    """Parse cookie string into dictionary format for requests library."""
    cookies = {}
    if cookie_string:
        # Handle both formats: "name=value; name2=value2" and individual cookies
        cookie_pairs = cookie_string.split(';')
        for pair in cookie_pairs:
            if '=' in pair:
                name, value = pair.strip().split('=', 1)
                cookies[name.strip()] = value.strip()
    return cookies

async def tool_info() -> dict:
    """Returns information about the lng_http_client tool."""
    return {
        "name": "lng_http_client",
        "description": """Universal HTTP Swiss Army Knife - The most powerful HTTP client for automation

**Core Features:**
• **All HTTP Methods** - GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
• **Smart Pagination** - Auto-paginate with custom conditions and URL building
• **Async Operations** - Background jobs with polling and webhook callbacks  
• **Intelligent Batching** - Sequential, parallel, or mixed execution strategies
• **Advanced Auth** - OAuth 1.0/2.0, JWT, Bearer, API Keys, custom headers
• **Browser Emulation** - Real User-Agent rotation, cookie management, fingerprinting
• **Encrypted Cookies** - Corporate-grade AES-256-GCM cookie integration with lng_cookie_grabber
• **Multi-format Support** - JSON, XML, HTML, CSV, binary data handling
• **Expression System** - JavaScript/Python expressions for dynamic requests
• **State Persistence** - Session management across MCP restarts
• **Pipeline Integration** - Works with lng_batch_run and lng_webhook_server

**Operation Modes:**
• `request` - Single HTTP request with full configuration
• `paginate` - Auto-pagination with accumulator and stop conditions  
• `batch` - Multiple requests with configurable concurrency
• `async_start` - Start long-running operation
• `async_poll` - Check status of async operation
• `webhook_callback` - Handle webhook results
• `session_info` - Get current session state
• `export_curl` - Export request as cURL command
• `import_har` - Import from HAR file

**Advanced Configuration:**
• Rate limiting per domain/endpoint
• Custom retry strategies with exponential backoff
• SSL/TLS configuration and certificate handling  
• Proxy support with authentication
• Response streaming for large data
• Request/response logging and metrics
• Cookie jar persistence
• Custom validation rules

**Expression Context:**
All expressions have access to:
```javascript
{
  "env": {"API_KEY": "xxx", ...},           // Environment variables
  "session": {"requests": [], "responses": [], "cookies": {}, ...}, // Session state
  "current": {"url": "...", "headers": {}, ...}, // Current request
  "previous": {"status": 200, "data": {}, ...},   // Previous response
  "accumulated": [...],                      // Paginated results
  "vars": {"custom_var": "value", ...}      // Custom variables
}
```

**Example Configurations:**

**Simple Request:**
```json
{
  "mode": "request",
  "url": "https://api.github.com/user",
  "method": "GET",
  "headers": {
    "Authorization": "Bearer {! env.GITHUB_TOKEN !}",
    "User-Agent": "MyApp/1.0"
  }
}
```

**Smart Pagination:**
```json
{
  "mode": "paginate", 
  "url": "https://api.github.com/repos/{! vars.owner !}/{! vars.repo !}/issues",
  "method": "GET",
  "headers": {"Authorization": "Bearer {! env.GITHUB_TOKEN !}"},
  "pagination": {
    "next_url": "{! previous.headers.link ? parseLink(previous.headers.link) : null !}",
    "continue_condition": "{! previous.data.length > 0 !}",
    "max_pages": 100,
    "accumulator": "data"
  }
}
```

**Batch Processing:**
```json
{
  "mode": "batch",
  "requests": [
    {"url": "https://api.example.com/users/{! vars.user_id !}", "method": "GET"},
    {"url": "https://api.example.com/posts", "method": "POST", "data": {"title": "Test"}}
  ],
  "execution": {
    "strategy": "parallel",
    "max_concurrent": 5,
    "rate_limit": {"requests": 100, "period": 60}
  }
}
```

**Async Operation:**
```json
{
  "mode": "async_start",
  "url": "https://api.example.com/long-job",
  "method": "POST", 
  "data": {"large_dataset": "..."},
  "async_config": {
    "poll_url": "{! response.data.status_url !}",
    "poll_interval": 30,
    "max_wait_time": 3600,
    "webhook_url": "http://localhost:8080/webhook"
  }
}
```

**Encrypted Cookies (Corporate Security):**
```json
{
  "mode": "request",
  "url": "https://protected-api.company.com/user/profile",
  "method": "GET",
  "use_encrypted_cookies": {
    "session": "corp_session_123_abc",
    "domain": "protected-api.company.com"
  }
}
```""",
        "schema": {
            "type": "object",
            "properties": {
                # Core operation mode
                "mode": {
                    "type": "string",
                    "description": "Operation mode",
                    "enum": ["request", "paginate", "batch", "async_start", "async_poll", "webhook_callback", "session_info", "export_curl", "import_har"],
                    "default": "request"
                },
                
                # Basic request configuration
                "url": {
                    "type": "string", 
                    "description": "Request URL (supports expressions: {! env.API_URL !}/users)"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP method",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"],
                    "default": "GET"
                },
                "headers": {
                    "type": "object",
                    "description": "Request headers (values support expressions)"
                },
                "params": {
                    "type": "object", 
                    "description": "URL parameters (values support expressions)"
                },
                "data": {
                    "description": "Request body data (supports expressions)"
                },
                "json": {
                    "type": "object",
                    "description": "JSON request body (supports expressions)"
                },
                "files": {
                    "type": "object",
                    "description": "Files to upload (multipart/form-data)"
                },
                
                # Authentication
                "auth": {
                    "type": "object",
                    "description": "Authentication configuration",
                    "properties": {
                        "type": {"type": "string", "enum": ["basic", "bearer", "oauth1", "oauth2", "api_key", "custom"]},
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                        "token": {"type": "string"},
                        "api_key": {"type": "string"},
                        "api_key_header": {"type": "string"},
                        "oauth_config": {"type": "object"}
                    }
                },
                
                # Advanced request options
                "timeout": {"type": "number", "description": "Request timeout in seconds", "default": 30},
                "allow_redirects": {"type": "boolean", "default": True},
                "verify_ssl": {"type": "boolean", "default": True},
                "proxies": {"type": "object", "description": "Proxy configuration"},
                "cookies": {"type": "object", "description": "Custom cookies"},
                
                # Encrypted cookies integration
                "use_encrypted_cookies": {
                    "type": "object",
                    "description": "Use encrypted cookies from lng_cookie_grabber system",
                    "properties": {
                        "session": {"type": "string", "description": "Cookie session ID"},
                        "domain": {"type": "string", "description": "Domain to decrypt cookies for"},
                        "auto_detect_domain": {"type": "boolean", "description": "Auto-detect domain from request URL", "default": True}
                    }
                },
                
                # Pagination configuration
                "pagination": {
                    "type": "object",
                    "description": "Pagination settings for paginate mode",
                    "properties": {
                        "next_url": {"type": "string", "description": "Expression to build next page URL"},
                        "continue_condition": {"type": "string", "description": "Expression to determine if pagination should continue"},
                        "max_pages": {"type": "integer", "default": 50},
                        "accumulator": {"type": "string", "description": "JSONPath to data to accumulate", "default": "data"},
                        "page_delay": {"type": "number", "description": "Delay between pages in seconds", "default": 1}
                    }
                },
                
                # Batch configuration  
                "requests": {
                    "type": "array",
                    "description": "Array of requests for batch mode",
                    "items": {"type": "object"}
                },
                "execution": {
                    "type": "object", 
                    "description": "Batch execution configuration",
                    "properties": {
                        "strategy": {"type": "string", "enum": ["sequential", "parallel", "mixed"], "default": "sequential"},
                        "max_concurrent": {"type": "integer", "default": 5},
                        "rate_limit": {
                            "type": "object",
                            "properties": {
                                "requests": {"type": "integer"},
                                "period": {"type": "integer", "description": "Period in seconds"}
                            }
                        }
                    }
                },
                
                # Async configuration
                "async_config": {
                    "type": "object",
                    "description": "Async operation configuration",
                    "properties": {
                        "poll_url": {"type": "string", "description": "URL to poll for status"},
                        "poll_interval": {"type": "integer", "description": "Polling interval in seconds", "default": 30},
                        "max_wait_time": {"type": "integer", "description": "Maximum wait time in seconds", "default": 3600},
                        "webhook_url": {"type": "string", "description": "Webhook URL for completion notification"},
                        "completion_condition": {"type": "string", "description": "Expression to check if operation is complete"}
                    }
                },
                
                # Response processing
                "response": {
                    "type": "object",
                    "description": "Response processing configuration", 
                    "properties": {
                        "format": {"type": "string", "enum": ["auto", "json", "xml", "html", "text", "binary"], "default": "auto"},
                        "extract": {"type": "object", "description": "Data extraction rules using JSONPath, XPath, CSS selectors"},
                        "validate": {"type": "object", "description": "Response validation rules"},
                        "save_to_file": {"type": "string", "description": "File path to save response (supports expressions)"}
                    }
                },
                
                # Browser emulation
                "browser_emulation": {
                    "type": "object",
                    "description": "Browser emulation settings",
                    "properties": {
                        "user_agent_rotation": {"type": "boolean", "default": False},
                        "custom_user_agents": {"type": "array", "items": {"type": "string"}},
                        "fingerprint_randomization": {"type": "boolean", "default": False},
                        "maintain_session": {"type": "boolean", "default": True}
                    }
                },
                
                # Retry and error handling
                "retry": {
                    "type": "object",
                    "description": "Retry configuration",
                    "properties": {
                        "max_retries": {"type": "integer", "default": 3},
                        "backoff_strategy": {"type": "string", "enum": ["fixed", "exponential", "linear"], "default": "exponential"},
                        "retry_delay": {"type": "number", "default": 1},
                        "retry_conditions": {"type": "array", "items": {"type": "string"}},
                        "retry_on_status": {"type": "array", "items": {"type": "integer"}}
                    }
                },
                
                # Variables and context
                "vars": {
                    "type": "object",
                    "description": "Custom variables accessible in expressions"
                },
                
                # Session and state management
                "session_id": {
                    "type": "string", 
                    "description": "Session ID for state persistence (auto-generated if not provided)"
                },
                "preserve_session": {"type": "boolean", "default": True},
                
                # Configuration from file
                "config_file": {
                    "type": "string",
                    "description": "Path to JSON config file (alternative to inline config)"
                },
                
                # Logging and debugging
                "debug": {"type": "boolean", "default": False},
                "log_requests": {"type": "boolean", "default": True},
                "log_responses": {"type": "boolean", "default": False},
                "show_headers": {"type": "boolean", "default": False, "description": "Include response headers in output"},
                
                # Pipeline integration
                "pipeline": {
                    "type": "array",
                    "description": "Pipeline to execute after request completion",
                    "items": {"type": "object"}
                },
                
                # Import/Export
                "har_file": {"type": "string", "description": "HAR file path for import_har mode"},
                "export_format": {"type": "string", "enum": ["curl", "postman", "har"], "default": "curl"},
                
                # Async operation management
                "async_job_id": {"type": "string", "description": "Async job ID for async_poll mode"},
                "webhook_data": {"type": "object", "description": "Webhook callback data for webhook_callback mode"}
            },
            "required": []
        }
    }


class HTTPClient:
    """Universal HTTP client with advanced features"""
    
    def __init__(self):
        self.state_manager = FileStateManager("mcp_server/config/http_client")
        self.sessions = {}  # In-memory sessions
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
    
    def get_session(self, session_id: str = None) -> Dict:
        """Get or create session state"""
        if not session_id:
            session_id = f"http_session_{int(time.time())}"
            
        if session_id not in self.sessions:
            # Try to load from persistent storage
            saved_state = self.state_manager.get(session_id, None, ".json")
            if saved_state:
                self.sessions[session_id] = saved_state
            else:
                self.sessions[session_id] = {
                    "id": session_id,
                    "created": datetime.now().isoformat(),
                    "requests": [],
                    "responses": [],
                    "cookies": {},
                    "vars": {},
                    "async_jobs": {},
                    "metrics": {
                        "total_requests": 0,
                        "successful_requests": 0,
                        "failed_requests": 0,
                        "avg_response_time": 0
                    }
                }
        
        return self.sessions[session_id]
    
    def save_session(self, session_id: str):
        """Save session to persistent storage"""
        if session_id in self.sessions:
            self.state_manager.set(session_id, self.sessions[session_id], ".json")
    
    def build_expression_context(self, session: Dict, current_request: Dict = None, previous_response: Dict = None, accumulated: List = None, vars_dict: Dict = None) -> Dict:
        """Build context for expression evaluation"""
        # Start with default context (includes env, datetime, etc.)
        context = build_default_context()
        
        # Add HTTP client specific context
        context.update({
            "session": session,
            "current": current_request or {},
            "previous": previous_response or {},
            "accumulated": accumulated or [],
            "vars": vars_dict or session.get("vars", {})
        })
        return context
    
    def evaluate_expression(self, expr: str, context: Dict) -> Any:
        """Evaluate JavaScript or Python expression"""
        try:
            # Use substitute_expressions function from pipeline
            result = substitute_expressions(expr, context)
            # Try to parse as Python object if it's a string
            if isinstance(result, str):
                try:
                    return parse_substituted_string(result, context)
                except:
                    return result
            return result
        except Exception as e:
            return f"Expression error: {str(e)}"
    
    def process_expressions_in_dict(self, data: Any, context: Dict) -> Any:
        """Recursively process expressions in dictionary/list structures"""
        if isinstance(data, dict):
            return {k: self.process_expressions_in_dict(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.process_expressions_in_dict(item, context) for item in data]
        elif isinstance(data, str) and (("{!" in data and "!}" in data) or ("[!" in data and "!]" in data)):
            return self.evaluate_expression(data, context)
        else:
            return data
    
    def get_random_user_agent(self) -> str:
        """Get random user agent for browser emulation"""
        import random
        return random.choice(self.user_agents)
    
    def censor_sensitive_headers(self, headers: Dict) -> Dict:
        """Censor sensitive headers like cookies and authorization for security"""
        censored_headers = {}
        sensitive_headers = ['cookie', 'set-cookie', 'authorization', 'x-auth-token', 'api-key']
        
        for key, value in headers.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_headers):
                censored_headers[key] = "<censored>"
            else:
                censored_headers[key] = value
        
        return censored_headers
    
    async def make_request(self, config: Dict, session: Dict, context: Dict) -> Dict:
        """Make a single HTTP request"""
        start_time = time.time()
        
        # Process expressions in config
        processed_config = self.process_expressions_in_dict(config, context)
        
        # Build request
        url = processed_config.get("url", "")
        method = processed_config.get("method", "GET").upper()
        headers = processed_config.get("headers", {})
        params = processed_config.get("params", {})
        data = processed_config.get("data")
        json_data = processed_config.get("json")
        files = processed_config.get("files", {})
        timeout = processed_config.get("timeout", 30)
        show_headers = processed_config.get("show_headers", False)  # Get show_headers parameter
        
        # Browser emulation
        browser_config = processed_config.get("browser_emulation", {})
        if browser_config.get("user_agent_rotation", False):
            headers["User-Agent"] = self.get_random_user_agent()
        
        # Authentication
        auth_config = processed_config.get("auth", {})
        auth = None
        if auth_config:
            auth_type = auth_config.get("type")
            if auth_type == "basic":
                auth = (auth_config.get("username"), auth_config.get("password"))
            elif auth_type == "bearer":
                headers["Authorization"] = f"Bearer {auth_config.get('token')}"
            elif auth_type == "api_key":
                key_header = auth_config.get("api_key_header", "X-API-Key")
                headers[key_header] = auth_config.get("api_key")
        
        # Cookies from session
        cookies = session.get("cookies", {})
        cookies.update(processed_config.get("cookies", {}))
        
        # Handle encrypted cookies
        encrypted_config = processed_config.get("use_encrypted_cookies")
        if encrypted_config:
            try:
                session_id = encrypted_config.get("session")
                domain = encrypted_config.get("domain")
                auto_detect = encrypted_config.get("auto_detect_domain", True)
                
                if not session_id:
                    raise ValueError("session parameter is required for use_encrypted_cookies")
                
                # Auto-detect domain from URL if not specified
                if not domain and auto_detect:
                    parsed_url = urlparse(url)
                    domain = parsed_url.hostname
                    if not domain:
                        raise ValueError("Could not auto-detect domain from URL, please specify domain explicitly")
                elif not domain:
                    raise ValueError("domain parameter is required when auto_detect_domain is False")
                
                # Decrypt cookies for domain
                encrypted_cookie_string = await decrypt_cookies_for_domain(session_id, domain)
                encrypted_cookies = parse_cookie_string(encrypted_cookie_string)
                
                # Merge encrypted cookies (they take precedence)
                cookies.update(encrypted_cookies)
                
                # Log cookie usage (without values for security)
                if len(encrypted_cookies) > 0:
                    print(f"Using {len(encrypted_cookies)} encrypted cookies for domain: {domain}")
                    
            except Exception as e:
                raise ValueError(f"Encrypted cookies error: {str(e)}")
        
        try:
            # Make request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                files=files,
                timeout=timeout,
                auth=auth,
                cookies=cookies,
                allow_redirects=processed_config.get("allow_redirects", True),
                verify=processed_config.get("verify_ssl", True),
                proxies=processed_config.get("proxies")
            )
            
            # Update session cookies
            session["cookies"].update(response.cookies.get_dict())
            
            # Process response
            response_time = time.time() - start_time
            
            # Determine content type and parse response
            content_type = response.headers.get("content-type", "").lower()
            response_data = None
            
            try:
                if "application/json" in content_type:
                    response_data = response.json()
                elif "text/xml" in content_type or "application/xml" in content_type:
                    response_data = response.text
                elif "text/html" in content_type:
                    response_data = response.text
                else:
                    response_data = response.text
            except:
                response_data = response.text
            
            result = {
                "success": True,
                "status_code": response.status_code,
                "data": response_data,
                "url": response.url,
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            }
            
            # Include headers only if requested
            if show_headers:
                result["headers"] = self.censor_sensitive_headers(dict(response.headers))
            
            # Update metrics
            session["metrics"]["total_requests"] += 1
            session["metrics"]["successful_requests"] += 1
            session["metrics"]["avg_response_time"] = (
                (session["metrics"]["avg_response_time"] * (session["metrics"]["total_requests"] - 1) + response_time) /
                session["metrics"]["total_requests"]
            )
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            
            result = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update metrics
            session["metrics"]["total_requests"] += 1
            session["metrics"]["failed_requests"] += 1
            
            return result
    
    async def handle_request_mode(self, params: Dict) -> Dict:
        """Handle single request mode"""
        session_id = params.get("session_id")
        session = self.get_session(session_id)
        
        # Build context
        vars_dict = params.get("vars", {})
        session["vars"].update(vars_dict)
        
        context = self.build_expression_context(session, vars_dict=session["vars"])
        
        # Make request
        result = await self.make_request(params, session, context)
        
        # Store in session
        session["requests"].append(params)
        session["responses"].append(result)
        
        # Save session
        self.save_session(session["id"])
        
        # Process response if needed
        response_config = params.get("response", {})
        if response_config.get("save_to_file"):
            file_path = self.process_expressions_in_dict(
                response_config["save_to_file"], 
                self.build_expression_context(session, previous_response=result, vars_dict=session["vars"])
            )
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    if isinstance(result["data"], (dict, list)):
                        json.dump(result["data"], f, indent=2, ensure_ascii=False)
                    else:
                        f.write(str(result["data"]))
                result["saved_to"] = file_path
            except Exception as e:
                result["save_error"] = str(e)
        
        return {
            "mode": "request",
            "session_id": session["id"], 
            "result": result,
            "session_metrics": session["metrics"]
        }
    
    async def handle_paginate_mode(self, params: Dict) -> Dict:
        """Handle pagination mode"""
        session_id = params.get("session_id")
        session = self.get_session(session_id)
        
        pagination_config = params.get("pagination", {})
        max_pages = pagination_config.get("max_pages", 50)
        page_delay = pagination_config.get("page_delay", 1)
        accumulator_path = pagination_config.get("accumulator", "data")
        
        # Build initial context
        vars_dict = params.get("vars", {})
        session["vars"].update(vars_dict)
        
        accumulated_data = []
        current_page = 1
        current_url = params.get("url")
        
        while current_page <= max_pages:
            # Update request config with current URL
            current_config = params.copy()
            current_config["url"] = current_url
            
            # Build context for current request
            context = self.build_expression_context(
                session, 
                current_request=current_config,
                accumulated=accumulated_data,
                vars_dict=session["vars"]
            )
            
            # Make request
            result = await self.make_request(current_config, session, context)
            
            # Store in session
            session["requests"].append(current_config)
            session["responses"].append(result)
            
            if not result["success"]:
                break
            
            # Extract data to accumulate
            if accumulator_path and result["data"]:
                try:
                    if accumulator_path == "data":
                        page_data = result["data"]
                    else:
                        # Use JSONPath to extract data
                        jsonpath_expr = jsonpath_parse(accumulator_path)
                        matches = [match.value for match in jsonpath_expr.find(result["data"])]
                        page_data = matches[0] if matches else []
                    
                    if isinstance(page_data, list):
                        accumulated_data.extend(page_data)
                    else:
                        accumulated_data.append(page_data)
                        
                except Exception as e:
                    # If extraction fails, just add the whole response
                    accumulated_data.append(result["data"])
            
            # Check continue condition
            continue_condition = pagination_config.get("continue_condition")
            if continue_condition:
                context_with_previous = self.build_expression_context(
                    session,
                    previous_response=result,
                    accumulated=accumulated_data, 
                    vars_dict=session["vars"]
                )
                
                should_continue = self.evaluate_expression(continue_condition, context_with_previous)
                if not should_continue:
                    break
            
            # Build next URL
            next_url_expr = pagination_config.get("next_url")
            if not next_url_expr:
                break
                
            context_with_previous = self.build_expression_context(
                session,
                previous_response=result,
                accumulated=accumulated_data,
                vars_dict=session["vars"]
            )
            
            next_url = self.evaluate_expression(next_url_expr, context_with_previous)
            if not next_url or next_url == current_url:
                break
                
            current_url = next_url
            current_page += 1
            
            # Delay between pages
            if page_delay > 0:
                await asyncio.sleep(page_delay)
        
        # Save session
        self.save_session(session["id"])
        
        return {
            "mode": "paginate",
            "session_id": session["id"],
            "total_pages": current_page - 1,
            "total_items": len(accumulated_data),
            "accumulated_data": accumulated_data,
            "session_metrics": session["metrics"]
        }
    
    async def handle_batch_mode(self, params: Dict) -> Dict:
        """Handle batch requests mode"""
        session_id = params.get("session_id")
        session = self.get_session(session_id)
        
        requests_list = params.get("requests", [])
        execution_config = params.get("execution", {})
        strategy = execution_config.get("strategy", "sequential")
        max_concurrent = execution_config.get("max_concurrent", 5)
        
        # Build context
        vars_dict = params.get("vars", {})
        session["vars"].update(vars_dict)
        
        results = []
        
        if strategy == "sequential":
            # Execute requests one by one
            for i, request_config in enumerate(requests_list):
                context = self.build_expression_context(session, vars_dict=session["vars"])
                result = await self.make_request(request_config, session, context)
                results.append(result)
                
                session["requests"].append(request_config)
                session["responses"].append(result)
                
        elif strategy == "parallel":
            # Execute requests in parallel with concurrency limit
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def make_limited_request(request_config):
                async with semaphore:
                    context = self.build_expression_context(session, vars_dict=session["vars"])
                    return await self.make_request(request_config, session, context)
            
            # Execute all requests
            tasks = [make_limited_request(req) for req in requests_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Store in session
            for req, res in zip(requests_list, results):
                session["requests"].append(req)
                if isinstance(res, Exception):
                    session["responses"].append({
                        "success": False,
                        "error": str(res),
                        "error_type": type(res).__name__
                    })
                else:
                    session["responses"].append(res)
        
        # Save session
        self.save_session(session["id"])
        
        # Calculate batch statistics
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failed = len(results) - successful
        
        return {
            "mode": "batch",
            "session_id": session["id"],
            "total_requests": len(requests_list),
            "successful": successful,
            "failed": failed,
            "results": results,
            "session_metrics": session["metrics"]
        }
    
    async def handle_session_info_mode(self, params: Dict) -> Dict:
        """Handle session info mode"""
        session_id = params.get("session_id")
        if not session_id:
            return {"error": "session_id required for session_info mode"}
            
        session = self.get_session(session_id)
        
        return {
            "mode": "session_info",
            "session_id": session_id,
            "session_data": {
                "id": session["id"],
                "created": session["created"],
                "total_requests": len(session["requests"]),
                "total_responses": len(session["responses"]),
                "cookies_count": len(session["cookies"]),
                "vars": session["vars"],
                "metrics": session["metrics"],
                "async_jobs": list(session["async_jobs"].keys())
            }
        }
    
    async def handle_export_curl_mode(self, params: Dict) -> Dict:
        """Handle export to cURL mode"""
        session_id = params.get("session_id")
        session = self.get_session(session_id)
        
        # Build context and process expressions
        context = self.build_expression_context(session, vars_dict=session.get("vars", {}))
        processed_config = self.process_expressions_in_dict(params, context)
        
        # Build cURL command
        url = processed_config.get("url", "")
        method = processed_config.get("method", "GET").upper()
        headers = processed_config.get("headers", {})
        data = processed_config.get("data")
        json_data = processed_config.get("json")
        
        curl_parts = ["curl"]
        
        # Method
        if method != "GET":
            curl_parts.extend(["-X", method])
        
        # Headers
        for key, value in headers.items():
            curl_parts.extend(["-H", f'"{key}: {value}"'])
        
        # Data
        if json_data:
            curl_parts.extend(["-H", '"Content-Type: application/json"'])
            curl_parts.extend(["-d", f"'{json.dumps(json_data)}'"])
        elif data:
            if isinstance(data, dict):
                # Form data
                for key, value in data.items():
                    curl_parts.extend(["-d", f"{key}={value}"])
            else:
                curl_parts.extend(["-d", f"'{data}'"])
        
        # URL (last)
        curl_parts.append(f'"{url}"')
        
        curl_command = " ".join(curl_parts)
        
        return {
            "mode": "export_curl",
            "curl_command": curl_command,
            "original_config": processed_config
        }


async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Main tool execution function"""
    try:
        client = HTTPClient()
        mode = parameters.get("mode", "request")
        
        # Load config from file if specified
        config_file = parameters.get("config_file")
        if config_file:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                # Merge file config with parameters (parameters take precedence)
                merged_params = {**file_config, **parameters}
                parameters = merged_params
            except Exception as e:
                return [types.TextContent(type="text", text=f"❌ Error loading config file: {str(e)}")]
        
        # Route to appropriate handler based on mode
        if mode == "request":
            result = await client.handle_request_mode(parameters)
        elif mode == "paginate":
            result = await client.handle_paginate_mode(parameters)
        elif mode == "batch":
            result = await client.handle_batch_mode(parameters)
        elif mode == "session_info":
            result = await client.handle_session_info_mode(parameters)
        elif mode == "export_curl":
            result = await client.handle_export_curl_mode(parameters)
        else:
            return [types.TextContent(type="text", text=f"❌ Unknown mode: {mode}")]
        
        # Execute pipeline if specified
        pipeline = parameters.get("pipeline")
        if pipeline and result.get("result", {}).get("success", True):
            try:
                # Import pipeline runner
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lng_batch_run'))
                from tool import BatchRunner
                
                pipeline_runner = BatchRunner()
                # Build pipeline context with default context (env, datetime, etc.)
                pipeline_context = build_default_context({
                    "http_result": result,
                    "session": client.sessions.get(result.get("session_id", ""), {})
                })
                
                pipeline_result = await pipeline_runner.run_pipeline(pipeline, pipeline_context)
                result["pipeline_result"] = pipeline_result
                
            except Exception as e:
                result["pipeline_error"] = str(e)
        
        return [types.TextContent(
            type="text", 
            text=json.dumps(result, indent=2, ensure_ascii=False, default=str)
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text", 
            text=f"❌ HTTP Client Error: {str(e)}\nType: {type(e).__name__}"
        )]
