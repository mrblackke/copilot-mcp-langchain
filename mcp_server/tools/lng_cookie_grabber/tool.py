import mcp.types as types
import json
import logging
import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import getpass

logger = logging.getLogger('mcp_server.tools.lng_cookie_grabber')

# Cryptographic constants for corporate-grade security
ENCRYPTION_KEY_LENGTH = 32  # AES-256
PBKDF2_ITERATIONS = 100000  # OWASP recommended minimum
TAG_LENGTH = 16  # GCM authentication tag

def secure_password_prompt(prompt_text: str) -> str:
    """Show secure password input dialog with enhanced MCP mode support."""
    import platform
    import subprocess
    
    try:
        if platform.system() == "Windows":
            # PowerShell password dialog for Windows
            logger.info("Using PowerShell password dialog (MCP mode)")
            
            powershell_script = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "Cookie Decryption - Corporate Security"
$form.Size = New-Object System.Drawing.Size(450,180)
$form.StartPosition = "CenterScreen"
$form.TopMost = $true
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false

$label1 = New-Object System.Windows.Forms.Label
$label1.Location = New-Object System.Drawing.Point(15,15)
$label1.Size = New-Object System.Drawing.Size(400,20)
$label1.Text = "{prompt_text}"
$label1.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$form.Controls.Add($label1)

$label2 = New-Object System.Windows.Forms.Label
$label2.Location = New-Object System.Drawing.Point(15,35)
$label2.Size = New-Object System.Drawing.Size(400,15)
$label2.Text = "Session: Browser Encrypted Cookies | Security: AES-256-GCM"
$label2.Font = New-Object System.Drawing.Font("Segoe UI", 8)
$label2.ForeColor = [System.Drawing.Color]::Gray
$form.Controls.Add($label2)

$passwordBox = New-Object System.Windows.Forms.TextBox
$passwordBox.Location = New-Object System.Drawing.Point(15,65)
$passwordBox.Size = New-Object System.Drawing.Size(400,25)
$passwordBox.PasswordChar = "*"
$passwordBox.Font = New-Object System.Drawing.Font("Consolas", 10)
$form.Controls.Add($passwordBox)

$okButton = New-Object System.Windows.Forms.Button
$okButton.Location = New-Object System.Drawing.Point(250,105)
$okButton.Size = New-Object System.Drawing.Size(80,30)
$okButton.Text = "OK"
$okButton.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$okButton.DialogResult = [System.Windows.Forms.DialogResult]::OK
$okButton.BackColor = [System.Drawing.Color]::LightBlue
$form.AcceptButton = $okButton
$form.Controls.Add($okButton)

$cancelButton = New-Object System.Windows.Forms.Button
$cancelButton.Location = New-Object System.Drawing.Point(340,105)
$cancelButton.Size = New-Object System.Drawing.Size(80,30)
$cancelButton.Text = "Cancel"
$cancelButton.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$cancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($cancelButton)

$passwordBox.Focus()
$result = $form.ShowDialog()

if ($result -eq [System.Windows.Forms.DialogResult]::OK -and $passwordBox.Text.Length -gt 0) {{
    $passwordBox.Text
}} else {{
    "CANCELLED"
}}

$form.Dispose()
'''
            
            try:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", powershell_script],
                    capture_output=True,
                    text=True,
                    timeout=120  # 2 minutes timeout
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    raw_output = result.stdout.strip()
                    # Clean PowerShell output - take only the last line (should be password or CANCELLED)
                    lines = raw_output.split('\n')
                    password = lines[-1].strip()
                    
                    if password == "CANCELLED":
                        raise ValueError("Password input cancelled")
                    logger.info("✅ Password entered successfully via PowerShell")
                    return password
                else:
                    raise Exception(f"PowerShell dialog failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                raise Exception("Password input dialog timed out")
            except Exception as ps_error:
                logger.warning(f"PowerShell dialog failed: {ps_error}")
                raise ps_error
        else:
            # Use console input for Linux/Mac
            logger.info("Using console password input")
            password = getpass.getpass(prompt_text + ": ")
            return password
            
    except Exception as e:
        logger.error(f"Failed to get password input via GUI/PowerShell: {e}")
        # Enhanced fallback with better MCP support
        try:
            logger.info("Attempting console fallback for password input")
            password = getpass.getpass(prompt_text + " (console fallback): ")
            return password
        except Exception as fallback_e:
            logger.error(f"Console fallback also failed: {fallback_e}")
            raise ValueError("Password input failed in both GUI and console modes")

async def decrypt_browser_data(encrypted_package: dict) -> str:
    """Decrypt browser-encrypted data using Web Crypto API compatible method."""
    try:
        logger.info("Starting browser data decryption in MCP mode")
        logger.info(f"Encrypted package keys: {list(encrypted_package.keys())}")
        
        # Get password from user (corporate paranoia mode - ALWAYS ask!)
        logger.info("Prompting user for decryption password...")
        password = secure_password_prompt("Enter password to decrypt browser-encrypted cookies")
        
        try:
            # For browser-encrypted data, we need to use the same method as browser
            # Browser uses PBKDF2 with salt, not master key
            
            # Get salt from package - browser sends as integer array
            salt = bytes(encrypted_package["salt"])
            logger.info(f"Salt length: {len(salt)} bytes")
            
            # Derive key using same method as browser (PBKDF2 only, no master key)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=ENCRYPTION_KEY_LENGTH,
                salt=salt,
                iterations=encrypted_package.get("iterations", PBKDF2_ITERATIONS),
                backend=default_backend()
            )
            
            decryption_key = kdf.derive(password.encode('utf-8'))
            logger.info(f"Key derived successfully, length: {len(decryption_key)} bytes")
            
        finally:
            # SECURITY: Clear password from memory immediately after use
            password = None
            import gc
            gc.collect()
        
        # Decode ciphertext and IV - browser sends as integer arrays
        ciphertext_bytes = bytes(encrypted_package["ciphertext"])
        iv_bytes = bytes(encrypted_package["iv"])
        logger.info(f"Ciphertext length: {len(ciphertext_bytes)}, IV length: {len(iv_bytes)}")
        
        # Browser AES-GCM includes auth tag in ciphertext (last 16 bytes)
        actual_ciphertext = ciphertext_bytes[:-TAG_LENGTH]
        tag = ciphertext_bytes[-TAG_LENGTH:]
        logger.info(f"Actual ciphertext length: {len(actual_ciphertext)}, Tag length: {len(tag)}")
        
        # Create cipher with tag for authentication
        cipher = Cipher(
            algorithms.AES(decryption_key),
            modes.GCM(iv_bytes, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt and verify
        plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()
        logger.info(f"Decryption successful, plaintext length: {len(plaintext)} bytes")
        
        return plaintext.decode('utf-8')
        
    except Exception as e:
        logger.error(f"Browser decryption failed: {e}")
        raise ValueError("Browser decryption failed - wrong password or corrupted data")

async def tool_info() -> dict:
    return {
        "description": """Cookie Grabber Tool for Managing WebSocket/Webhook Servers and Processing Cookie Data.

**Universal Cookie Grabber Management System**
Complete solution for cookie collection with Chrome extension and server management.

**Operations:**
• `start` - Start webhook and websocket servers for cookie collection (stops existing first)
• `stop` - Stop webhook and websocket servers
• `decrypt` - Decrypt saved cookie data for use in HTTP requests  
• `store_encrypted` - Store pre-encrypted cookie data from browser
• `list_sessions` - List all available cookie sessions by scanning the cookies directory

**Features:**
**Direct Server Management** - Direct Python imports for deterministic control
**Cookie Processing** - Parse and organize cookie data by domain
**File Organization** - Save cookies to config/cookies/<sessionId>/<domain>.txt
**Session Support** - Support for sessionId-based cookie organization
**Error Handling** - Comprehensive error handling and logging

**Start Operation:**
Starts both webhook (port 9000) and websocket (port 9001) servers using 
the configuration files from the cookie grabber directory. Automatically
stops existing servers first for clean restart.

**Stop Operation:**
Stops both webhook and websocket servers cleanly.

**Store Encrypted Operation:**
Receives and stores pre-encrypted cookie data from browser.
Browser performs AES-256-GCM encryption with user password,
server just organizes and saves the encrypted files.

**Decrypt Operation:**
Decrypts cookie data for use in HTTP requests. Shows secure password
prompt for each decryption (corporate paranoia mode).

**Example Usage:**

Start servers:
```json
{
  "operation": "start"
}
```

Decrypt cookies:
```json
{
  "operation": "decrypt",
  "session": "my_session_123", 
  "domain": "domain1.com"
}
```

Store pre-encrypted cookies:
```json
{
  "operation": "store_encrypted",
  "encrypted_data": "{\"type\":\"encrypted_cookies\",\"sessionId\":\"...\",\"encrypted\":{...}}",
  "session": "my_session_123"
}
```

List sessions:
```json
{
  "operation": "list_sessions"
}
```

Stop servers:
```json
{
  "operation": "stop"
}
```
""",
        "schema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Operation to perform",
                    "enum": ["start", "stop", "decrypt", "store_encrypted", "list_sessions"]
                },
                "cookies": {
                    "type": "string", 
                    "description": "DEPRECATED - Cookie data (legacy process operation)"
                },
                "session": {
                    "type": "string",
                    "description": "Session ID for organizing cookie files (required for 'decrypt', 'store_encrypted' operations)"
                },
                "domain": {
                    "type": "string",
                    "description": "Domain to decrypt cookies for (required for 'decrypt' operation)"
                },
                "encrypted_data": {
                    "type": "string",
                    "description": "Pre-encrypted cookie data from browser (required for 'store_encrypted' operation)"
                }
            },
            "required": ["operation"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Execute cookie grabber operations."""
    
    try:
        operation = parameters.get("operation")
        
        if operation == "start":
            return await start_servers()
        elif operation == "stop":
            return await stop_servers()
        elif operation == "decrypt":
            session = parameters.get("session")
            domain = parameters.get("domain")
            
            if not session:
                raise ValueError("'session' parameter is required for decrypt operation")
            if not domain:
                raise ValueError("'domain' parameter is required for decrypt operation")
                
            return await decrypt_cookies(session, domain)
        elif operation == "store_encrypted":
            encrypted_data = parameters.get("encrypted_data")
            session = parameters.get("session")
            
            if not encrypted_data:
                raise ValueError("'encrypted_data' parameter is required for store_encrypted operation")
            if not session:
                raise ValueError("'session' parameter is required for store_encrypted operation")
                
            return await store_encrypted_cookies(encrypted_data, session)
        elif operation == "list_sessions":
            return await list_sessions()
        else:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }, indent=2)
            )]
            
    except Exception as e:
        logger.error(f"Error in lng_cookie_grabber: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]

async def start_servers() -> list[types.Content]:
    """Start webhook and websocket servers. Stops existing servers first."""
    try:
        logger.info("Starting cookie grabber servers (stopping existing first)...")
        
        # Stop existing servers first
        try:
            await stop_servers()
            logger.info("Existing servers stopped")
        except Exception as e:
            logger.warning(f"Error stopping existing servers (may not exist): {e}")
        
        results = []
        
        # Start webhook server
        try:
            from ..lng_webhook_server.tool import run_tool as run_webhook_tool
            
            webhook_params = {
                "operation": "start",
                "config_file": "mcp_server/tools/lng_cookie_grabber/webhook.json",
                "name": "cookie-status-server",
                "thread_mode": True
            }
            
            webhook_result = await run_webhook_tool("lng_webhook_server", webhook_params)
            webhook_data = json.loads(webhook_result[0].text)
            results.append({
                "service": "webhook",
                "status": "started" if webhook_data.get("success") else "failed",
                "details": webhook_data
            })
            
            logger.info(f"Webhook server: {webhook_data.get('message', 'Unknown result')}")
            
        except Exception as e:
            logger.error(f"Failed to start webhook server: {e}")
            results.append({
                "service": "webhook", 
                "status": "failed",
                "error": str(e)
            })
        
        # Start websocket server
        try:
            from ..lng_websocket_server.tool import run_tool as run_websocket_tool
            
            websocket_params = {
                "operation": "server_start",
                "config_file": "mcp_server/tools/lng_cookie_grabber/websocket.json",
                "name": "cookie-websocket-server"
            }
            
            websocket_result = await run_websocket_tool("lng_websocket_server", websocket_params)
            websocket_data = json.loads(websocket_result[0].text)
            results.append({
                "service": "websocket",
                "status": "started" if websocket_data.get("success") else "failed", 
                "details": websocket_data
            })
            
            logger.info(f"WebSocket server: {websocket_data.get('message', 'Unknown result')}")
            
        except Exception as e:
            logger.error(f"Failed to start websocket server: {e}")
            results.append({
                "service": "websocket",
                "status": "failed", 
                "error": str(e)
            })
        
        # Determine overall success
        all_started = all(r["status"] == "started" for r in results)
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": all_started,
                "message": f"Cookie grabber servers {'started successfully' if all_started else 'failed to start'}",
                "operation": "start",
                "timestamp": datetime.now().isoformat(),
                "services": results
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to start cookie grabber servers: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e),
                "operation": "start"
            }, indent=2)
        )]

async def stop_servers() -> list[types.Content]:
    """Stop webhook and websocket servers."""
    try:
        logger.info("Stopping cookie grabber servers...")
        
        results = []
        
        # Stop webhook server
        try:
            from ..lng_webhook_server.tool import run_tool as run_webhook_tool
            
            webhook_params = {
                "operation": "stop",
                "name": "cookie-status-server"
            }
            
            webhook_result = await run_webhook_tool("lng_webhook_server", webhook_params)
            webhook_data = json.loads(webhook_result[0].text)
            results.append({
                "service": "webhook",
                "status": "stopped" if webhook_data.get("success") else "failed",
                "details": webhook_data
            })
            
            logger.info(f"Webhook server: {webhook_data.get('message', 'Unknown result')}")
            
        except Exception as e:
            logger.error(f"Failed to stop webhook server: {e}")
            results.append({
                "service": "webhook",
                "status": "failed",
                "error": str(e)
            })
        
        # Stop websocket server
        try:
            from ..lng_websocket_server.tool import run_tool as run_websocket_tool
            
            websocket_params = {
                "operation": "server_stop", 
                "name": "cookie-websocket-server"
            }
            
            websocket_result = await run_websocket_tool("lng_websocket_server", websocket_params)
            websocket_data = json.loads(websocket_result[0].text)
            results.append({
                "service": "websocket",
                "status": "stopped" if websocket_data.get("success") else "failed",
                "details": websocket_data
            })
            
            logger.info(f"WebSocket server: {websocket_data.get('message', 'Unknown result')}")
            
        except Exception as e:
            logger.error(f"Failed to stop websocket server: {e}")
            results.append({
                "service": "websocket",
                "status": "failed",
                "error": str(e)
            })
        
        # Determine overall success  
        all_stopped = all(r["status"] == "stopped" for r in results)
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": all_stopped,
                "message": f"Cookie grabber servers {'stopped successfully' if all_stopped else 'failed to stop'}",
                "operation": "stop",
                "timestamp": datetime.now().isoformat(),
                "services": results
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to stop cookie grabber servers: {e}")
        return [types.TextContent(
            type="text", 
            text=json.dumps({
                "success": False,
                "error": str(e),
                "operation": "stop"
            }, indent=2)
        )]

async def decrypt_cookies(session: str, domain: str) -> list[types.Content]:
    """Decrypt cookie data for use in HTTP requests (corporate paranoia mode)."""
    try:
        logger.info(f"Decrypting cookies for session: {session}, domain: {domain}")
        
        # Look for browser-encrypted file first (new format)
        browser_encrypted_file = f"mcp_server/config/cookies/{session}/all_domains.encrypted"
        
        if os.path.exists(browser_encrypted_file):
            # Handle browser-encrypted format
            logger.info("Found browser-encrypted file, processing...")
            
            # Load encrypted storage package
            with open(browser_encrypted_file, 'r', encoding='utf-8') as f:
                storage_package = json.load(f)
            
            # Extract encrypted data from storage package
            encrypted_package = storage_package.get("encrypted_data")
            if not encrypted_package:
                raise ValueError("Invalid storage package format")
            
            # Browser data is already in correct format - pass directly to decrypt_browser_data
            decrypted_cookies = await decrypt_browser_data(encrypted_package)
            
            # Parse decrypted cookies to extract specific domain or all domains
            cookie_lines = decrypted_cookies.strip().split('\n')
            
            if domain == 'all_domains':
                # Return all cookies from all domains
                domain_cookies = decrypted_cookies.strip()
                success_message = f"Successfully decrypted cookies for all domains (browser encryption)"
            else:
                # Look for specific domain
                domain_cookies = None
                for i, line in enumerate(cookie_lines):
                    if line.strip() == domain:
                        # Found the domain, next line should be cookies
                        if i + 1 < len(cookie_lines):
                            domain_cookies = cookie_lines[i + 1]
                            break
                
                if not domain_cookies:
                    raise ValueError(f"No cookies found for domain '{domain}' in decrypted data")
                    
                success_message = f"Successfully decrypted cookies for domain '{domain}' (browser encryption)"
            
            # Clear password from memory immediately
            password = None
            
            result = {
                "success": True,
                "message": success_message,
                "operation": "decrypt",
                "session": session,
                "domain": domain,
                "timestamp": datetime.now().isoformat(),
                "cookies": domain_cookies,
                "cookie_length": len(domain_cookies),
                "encryption_source": "browser",
                "security_note": "Cookies decrypted in memory - will be cleared after use"
            }
            
        else:
            # No encrypted cookies found for this session/domain
            raise ValueError(f"No encrypted cookies found for domain '{domain}' in session '{session}'")
        
        logger.info(f"Decrypted {len(result['cookies'])} characters of cookie data for {domain}")
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to decrypt cookies: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e),
                "operation": "decrypt",
                "session": session,
                "domain": domain
            }, indent=2)
        )]

async def store_encrypted_cookies(encrypted_data: str, session: str) -> list[types.Content]:
    """Store pre-encrypted cookie data from browser (browser-side encryption)."""
    try:
        logger.info(f"Storing pre-encrypted cookies for session: {session}")
        
        # Parse encrypted message from browser
        try:
            encrypted_message = json.loads(encrypted_data)
            if encrypted_message.get('type') != 'encrypted_cookies':
                raise ValueError("Invalid encrypted message format")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in encrypted_data")
        
        # Extract data from message
        sessionId = encrypted_message.get('sessionId', session)
        encrypted_package = encrypted_message.get('encrypted')
        domains_count = encrypted_message.get('domains_count', 0)
        timestamp = encrypted_message.get('timestamp')
        
        # Create session directory
        session_dir = f"mcp_server/config/cookies/{sessionId}"
        os.makedirs(session_dir, exist_ok=True)
        
        # Save encrypted package as a single file for the session
        encrypted_file = os.path.join(session_dir, "all_domains.encrypted")
        
        # Enhance encrypted package with metadata
        storage_package = {
            "encrypted_data": encrypted_package,
            "metadata": {
                "encrypted_by": "browser",
                "encryption_method": "AES-256-GCM + PBKDF2",
                "domains_count": domains_count,
                "timestamp": timestamp,
                "session_id": sessionId,
                "version": "1.0"
            }
        }
        
        with open(encrypted_file, 'w', encoding='utf-8') as f:
            json.dump(storage_package, f, indent=2)
        
        logger.info(f"Stored encrypted cookies for {domains_count} domains in {encrypted_file}")
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "message": f"Successfully stored encrypted cookies for {domains_count} domains",
                "operation": "store_encrypted", 
                "session": sessionId,
                "timestamp": datetime.now().isoformat(),
                "encrypted_file": encrypted_file,
                "domains_count": domains_count,
                "encryption_source": "browser",
                "security_level": "Corporate (Browser AES-256-GCM + PBKDF2)"
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to store encrypted cookies: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e),
                "operation": "store_encrypted",
                "session": session
            }, indent=2)
        )]

async def list_sessions() -> list[types.Content]:
    """List all available cookie sessions by scanning the cookies directory."""
    try:
        logger.info("Scanning for available cookie sessions...")
        
        cookies_base_dir = "mcp_server/config/cookies"
        
        if not os.path.exists(cookies_base_dir):
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": "No cookie sessions found - cookies directory does not exist",
                    "operation": "list_sessions",
                    "timestamp": datetime.now().isoformat(),
                    "sessions": []
                }, indent=2)
            )]
        
        sessions = []
        
        # Scan cookies directory for session folders
        for item in os.listdir(cookies_base_dir):
            session_path = os.path.join(cookies_base_dir, item)
            
            if os.path.isdir(session_path):
                session_info = {
                    "session_id": item,
                    "path": session_path,
                    "files": [],
                    "domains": [],
                    "created_at": None,
                    "modified_at": None,
                    "encryption_type": "unknown",
                    "total_size": 0
                }
                
                # Get directory timestamps
                stat = os.stat(session_path)
                session_info["created_at"] = datetime.fromtimestamp(stat.st_ctime).isoformat()
                session_info["modified_at"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                # Scan session directory for cookie files
                try:
                    for file_item in os.listdir(session_path):
                        file_path = os.path.join(session_path, file_item)
                        
                        if os.path.isfile(file_path):
                            file_stat = os.stat(file_path)
                            file_size = file_stat.st_size
                            session_info["total_size"] += file_size
                            
                            file_info = {
                                "name": file_item,
                                "size": file_size,
                                "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                            }
                            
                            session_info["files"].append(file_info)
                            
                            # Determine encryption type and extract domains
                            if file_item == "all_domains.encrypted":
                                session_info["encryption_type"] = "browser_encrypted"
                                
                                # Try to extract metadata from encrypted file
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        storage_package = json.load(f)
                                        
                                    metadata = storage_package.get("metadata", {})
                                    domains_count = metadata.get("domains_count", 0)
                                    
                                    session_info["domains_count"] = domains_count
                                    session_info["encryption_method"] = metadata.get("encryption_method", "AES-256-GCM + PBKDF2")
                                    session_info["encrypted_by"] = metadata.get("encrypted_by", "browser")
                                    session_info["version"] = metadata.get("version", "unknown")
                                    
                                except Exception as e:
                                    logger.warning(f"Could not read metadata from {file_path}: {e}")
                                    session_info["metadata_error"] = str(e)
                            
                            elif file_item.endswith(".txt"):
                                # Legacy plain text format
                                session_info["encryption_type"] = "plaintext"
                                domain = file_item.replace(".txt", "")
                                session_info["domains"].append(domain)
                
                except Exception as e:
                    logger.warning(f"Could not scan session directory {session_path}: {e}")
                    session_info["scan_error"] = str(e)
                
                sessions.append(session_info)
        
        # Sort sessions by modified date (newest first)
        sessions.sort(key=lambda x: x.get("modified_at", ""), reverse=True)
        
        logger.info(f"Found {len(sessions)} cookie sessions")
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "message": f"Found {len(sessions)} cookie sessions",
                "operation": "list_sessions",
                "timestamp": datetime.now().isoformat(),
                "cookies_directory": cookies_base_dir,
                "sessions_count": len(sessions),
                "sessions": sessions
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to list cookie sessions: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e),
                "operation": "list_sessions"
            }, indent=2)
        )]
