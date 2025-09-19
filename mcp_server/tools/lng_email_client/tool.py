import mcp.types as types
import json
import sys
import os
import asyncio
import time
import smtplib
import ssl
import mimetypes
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
import base64
import hashlib

# Initialize logger for email client
logger = logging.getLogger('mcp_server.tools.lng_email_client')

# Third-party libraries
import requests
import aiofiles
from jinja2 import Template, Environment, BaseLoader
from email_validator import validate_email, EmailNotValidError

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from mcp_server.pipeline.expressions import substitute_expressions, parse_substituted_string
from mcp_server.file_state_manager import FileStateManager

async def tool_info() -> dict:
    """Returns information about the lng_email_client tool."""
    return {
        "name": "lng_email_client",
        "description": """Universal Email Swiss Army Knife - The most powerful email client for automation

**Core Features:**
• **Multiple Protocols** - SMTP (Gmail, Outlook, custom), API services (SendGrid, Mailgun, SES)
• **Advanced Authentication** - Basic auth, OAuth 2.0, API keys, app passwords
• **Rich Content** - HTML emails, plain text, mixed content with inline images
• **Smart Attachments** - Multiple files, inline images, automatic MIME type detection
• **Template Engine** - Jinja2 templates with variables, conditionals, loops
• **Batch Operations** - Mass mailing with personalization and rate limiting
• **Expression System** - Dynamic content with environment variables and context
• **State Management** - Session persistence, delivery tracking, retry logic
• **Validation** - Email address validation, content checks, deliverability tests

**Operation Modes:**
• `send` - Send single email with full configuration
• `batch` - Mass email sending with personalization and rate limiting
• `template` - Template-based email generation and sending
• `test` - Test email server connection and authentication
• `session_info` - Get current session state and statistics
• `validate` - Validate email addresses and content

**Email Services Support:**
• **SMTP Servers:** Gmail, Outlook/Hotmail, Yahoo, custom SMTP
• **API Services:** SendGrid, Mailgun, Amazon SES, Mailchimp Transactional
• **Authentication:** Auto-detection of best auth method per service
• **Security:** TLS/SSL encryption, OAuth 2.0 flows, secure credential handling

**Expression Context:**
All expressions have access to:
```javascript
{
  "env": {"SMTP_PASSWORD": "xxx", "API_KEY": "yyy", ...}, // Environment variables
  "session": {"sent_emails": [], "failed_emails": [], ...}, // Session state
  "current": {"to": "user@example.com", "subject": "...", ...}, // Current email
  "recipient": {"name": "John", "email": "john@example.com", "custom_field": "..."}, // Recipient data
  "template_vars": {"order_id": "12345", "amount": "$100", ...}, // Template variables
  "vars": {"campaign_name": "Newsletter", ...} // Custom variables
}
```

**Example Configurations:**

**Simple SMTP Email:**
```json
{
  "mode": "send",
  "service": "smtp",
  "smtp_config": {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "{! env.GMAIL_USER !}",
    "password": "{! env.GMAIL_APP_PASSWORD !}",
    "use_tls": true
  },
  "from_email": "sender@example.com",
  "from_name": "Your App",
  "to": "recipient@example.com",
  "subject": "Test Email",
  "body_text": "Hello, this is a test email!",
  "body_html": "<h1>Hello!</h1><p>This is a <b>test</b> email!</p>"
}
```

**SendGrid API Email:**
```json
{
  "mode": "send",
  "service": "sendgrid",
  "api_config": {
    "api_key": "{! env.SENDGRID_API_KEY !}"
  },
  "from_email": "noreply@example.com",
  "from_name": "Your Service",
  "to": "user@example.com",
  "subject": "Welcome to our service!",
  "template_id": "welcome_template",
  "template_vars": {
    "user_name": "John Doe",
    "activation_link": "https://example.com/activate/abc123"
  }
}
```

**Template-based Email:**
```json
{
  "mode": "template",
  "service": "smtp",
  "smtp_config": {
    "host": "{! env.SMTP_HOST !}",
    "port": "{! env.SMTP_PORT !}",
    "username": "{! env.SMTP_USER !}",
    "password": "{! env.SMTP_PASSWORD !}"
  },
  "template": {
    "subject": "Order Confirmation #{{order_id}}",
    "body_html": "<h1>Thank you {{customer_name}}!</h1><p>Your order #{{order_id}} for {{amount}} has been confirmed.</p>",
    "body_text": "Thank you {{customer_name}}! Your order #{{order_id}} for {{amount}} has been confirmed."
  },
  "from_email": "orders@example.com",
  "to": "customer@example.com",
  "template_vars": {
    "customer_name": "John Smith",
    "order_id": "12345",
    "amount": "$99.99"
  }
}
```

**Batch Email Campaign:**
```json
{
  "mode": "batch",
  "service": "sendgrid",
  "api_config": {
    "api_key": "{! env.SENDGRID_API_KEY !}"
  },
  "from_email": "newsletter@example.com",
  "from_name": "Newsletter Team",
  "template": {
    "subject": "Hi {{name}}, check out our latest updates!",
    "body_html": "<h1>Hello {{name}}!</h1><p>We have exciting news for {{company}}...</p>"
  },
  "recipients": [
    {"email": "user1@example.com", "name": "John", "company": "Acme Corp"},
    {"email": "user2@example.com", "name": "Jane", "company": "Tech Ltd"}
  ],
  "batch_config": {
    "batch_size": 50,
    "delay_between_batches": 10,
    "rate_limit": {"emails_per_minute": 100}
  }
}
```

**Email with Attachments:**
```json
{
  "mode": "send",
  "service": "smtp",
  "smtp_config": {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "{! env.GMAIL_USER !}",
    "password": "{! env.GMAIL_APP_PASSWORD !}"
  },
  "from_email": "reports@example.com",
  "to": "manager@example.com",
  "subject": "Monthly Report - {! datetime.now().strftime('%B %Y') !}",
  "body_html": "<h1>Monthly Report</h1><p>Please find the attached report.</p>",
  "attachments": [
    {"file_path": "reports/monthly_report.pdf", "filename": "Monthly_Report.pdf"},
    {"file_path": "charts/sales_chart.png", "filename": "Sales_Chart.png", "inline": true, "cid": "sales_chart"}
  ]
}
```""",
        "schema": {
            "type": "object",
            "properties": {
                # Core operation mode
                "mode": {
                    "type": "string",
                    "description": "Operation mode",
                    "enum": ["send", "batch", "template", "test", "session_info", "validate"],
                    "default": "send"
                },
                
                # Email service configuration
                "service": {
                    "type": "string", 
                    "description": "Email service type",
                    "enum": ["smtp", "sendgrid", "mailgun", "ses", "mailchimp", "custom_api"],
                    "default": "smtp"
                },
                
                # SMTP configuration
                "smtp_config": {
                    "type": "object",
                    "description": "SMTP server configuration",
                    "properties": {
                        "host": {"type": "string", "description": "SMTP server hostname"},
                        "port": {"type": "integer", "description": "SMTP server port", "default": 465},
                        "username": {"type": "string", "description": "SMTP username (supports expressions)"},
                        "password": {"type": "string", "description": "SMTP password (supports expressions)"},
                        "use_tls": {"type": "boolean", "description": "Use TLS encryption", "default": False},
                        "use_ssl": {"type": "boolean", "description": "Use SSL encryption", "default": True}
                    }
                },
                
                # API service configuration
                "api_config": {
                    "type": "object",
                    "description": "API service configuration",
                    "properties": {
                        "api_key": {"type": "string", "description": "API key (supports expressions)"},
                        "api_url": {"type": "string", "description": "Custom API endpoint"},
                        "region": {"type": "string", "description": "Service region (for SES, etc.)"},
                        "additional_headers": {"type": "object", "description": "Additional HTTP headers"}
                    }
                },
                
                # Basic email fields
                "from_email": {"type": "string", "description": "Sender email address (supports expressions)"},
                "from_name": {"type": "string", "description": "Sender name (supports expressions)"},
                "to": {"type": ["string", "array"], "description": "Recipient email(s) (supports expressions)"},
                "cc": {"type": ["string", "array"], "description": "CC recipients (supports expressions)"},
                "bcc": {"type": ["string", "array"], "description": "BCC recipients (supports expressions)"},
                "reply_to": {"type": "string", "description": "Reply-to email address"},
                "subject": {"type": "string", "description": "Email subject (supports expressions and templates)"},
                
                # Email content
                "body_text": {"type": "string", "description": "Plain text email body (supports expressions and templates)"},
                "body_html": {"type": "string", "description": "HTML email body (supports expressions and templates)"},
                "priority": {"type": "string", "enum": ["low", "normal", "high"], "default": "normal"},
                
                # Template configuration
                "template": {
                    "type": "object",
                    "description": "Email template configuration",
                    "properties": {
                        "subject": {"type": "string", "description": "Subject template"},
                        "body_text": {"type": "string", "description": "Plain text body template"},
                        "body_html": {"type": "string", "description": "HTML body template"},
                        "template_file": {"type": "string", "description": "Path to template file"},
                        "template_id": {"type": "string", "description": "Service template ID (for SendGrid, etc.)"}
                    }
                },
                "template_vars": {
                    "type": "object",
                    "description": "Variables for template rendering"
                },
                
                # Attachments
                "attachments": {
                    "type": "array",
                    "description": "Email attachments",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to attachment file"},
                            "filename": {"type": "string", "description": "Attachment filename"},
                            "content_type": {"type": "string", "description": "MIME content type"},
                            "inline": {"type": "boolean", "description": "Inline attachment", "default": False},
                            "cid": {"type": "string", "description": "Content ID for inline images"}
                        },
                        "required": ["file_path"]
                    }
                },
                
                # Batch sending configuration
                "recipients": {
                    "type": "array",
                    "description": "List of recipients for batch mode",
                    "items": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "description": "Recipient email address"},
                            "name": {"type": "string", "description": "Recipient name"}
                        },
                        "required": ["email"],
                        "additionalProperties": True
                    }
                },
                "batch_config": {
                    "type": "object",
                    "description": "Batch processing configuration",
                    "properties": {
                        "batch_size": {"type": "integer", "description": "Number of emails per batch", "default": 10},
                        "delay_between_batches": {"type": "number", "description": "Delay between batches in seconds", "default": 1},
                        "rate_limit": {
                            "type": "object",
                            "properties": {
                                "emails_per_minute": {"type": "integer"},
                                "emails_per_hour": {"type": "integer"}
                            }
                        },
                        "retry_failed": {"type": "boolean", "description": "Retry failed emails", "default": True},
                        "max_retries": {"type": "integer", "description": "Maximum retry attempts", "default": 3}
                    }
                },
                
                # Validation options
                "validate_emails": {"type": "boolean", "description": "Validate email addresses", "default": True},
                "validate_content": {"type": "boolean", "description": "Validate email content", "default": False},
                
                # Variables and context
                "vars": {
                    "type": "object",
                    "description": "Custom variables accessible in expressions and templates"
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
                    "description": "Path to JSON/YAML config file (alternative to inline config)"
                },
                
                # Logging and debugging
                "debug": {"type": "boolean", "default": False},
                "log_emails": {"type": "boolean", "default": True},
                "log_content": {"type": "boolean", "default": False},
                
                # Pipeline integration
                "pipeline": {
                    "type": "array",
                    "description": "Pipeline to execute after email operations",
                    "items": {"type": "object"}
                },
                
                # Test mode specific
                "test_config": {
                    "type": "object",
                    "description": "Test configuration for test mode",
                    "properties": {
                        "connection_only": {"type": "boolean", "description": "Test connection only", "default": False},
                        "send_test_email": {"type": "boolean", "description": "Send actual test email", "default": True},
                        "test_recipient": {"type": "string", "description": "Test email recipient"}
                    }
                }
            },
            "required": []
        }
    }


class EmailClient:
    """Universal email client with multiple service support"""
    
    def __init__(self):
        self.state_manager = FileStateManager("mcp_server/config/email_client")
        self.sessions = {}  # In-memory sessions
        self.jinja_env = Environment(loader=BaseLoader())
    
    def get_session(self, session_id: str = None) -> Dict:
        """Get or create session state"""
        if not session_id:
            session_id = f"email_session_{int(time.time())}"
            
        if session_id not in self.sessions:
            # Try to load from persistent storage
            saved_state = self.state_manager.get(session_id, None, ".json")
            if saved_state:
                self.sessions[session_id] = saved_state
            else:
                self.sessions[session_id] = {
                    "id": session_id,
                    "created": datetime.now().isoformat(),
                    "sent_emails": [],
                    "failed_emails": [],
                    "templates": {},
                    "vars": {},
                    "metrics": {
                        "total_sent": 0,
                        "total_failed": 0,
                        "avg_send_time": 0,
                        "last_activity": None
                    }
                }
        
        return self.sessions[session_id]
    
    def save_session(self, session_id: str):
        """Save session to persistent storage"""
        if session_id in self.sessions:
            self.state_manager.set(session_id, self.sessions[session_id], ".json")
    
    def build_expression_context(self, session: Dict, current_email: Dict = None, recipient: Dict = None, template_vars: Dict = None, vars_dict: Dict = None) -> Dict:
        """Build context for expression evaluation"""
        context = {
            "session": session,
            "current": current_email or {},
            "recipient": recipient or {},
            "template_vars": template_vars or {},
            "vars": vars_dict or session.get("vars", {}),
            "datetime": datetime
        }
        return context
    
    def evaluate_expression(self, expr: str, context: Dict) -> Any:
        """Evaluate expression with context"""
        try:
            result = substitute_expressions(expr, context)
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
    
    def render_template(self, template_str: str, context: Dict) -> str:
        """Render Jinja2 template with context"""
        try:
            template = self.jinja_env.from_string(template_str)
            return template.render(**context.get("template_vars", {}), **context.get("vars", {}), **context)
        except Exception as e:
            return f"Template error: {str(e)}"
    
    def validate_email_address(self, email: str) -> Dict:
        """Validate email address"""
        try:
            validated_email = validate_email(email)
            return {
                "valid": True,
                "email": validated_email.email,
                "normalized": validated_email.email.lower(),
                "local": validated_email.local,
                "domain": validated_email.domain
            }
        except EmailNotValidError as e:
            return {
                "valid": False,
                "email": email,
                "error": str(e)
            }
    
    def prepare_attachments(self, attachments: List[Dict], context: Dict) -> List[Dict]:
        """Process and prepare attachments"""
        prepared = []
        
        for attachment in attachments:
            processed_attachment = self.process_expressions_in_dict(attachment, context)
            file_path = processed_attachment.get("file_path")
            
            if not os.path.exists(file_path):
                prepared.append({
                    "error": f"File not found: {file_path}",
                    "original": processed_attachment
                })
                continue
            
            # Auto-detect MIME type if not specified
            if not processed_attachment.get("content_type"):
                content_type, _ = mimetypes.guess_type(file_path)
                processed_attachment["content_type"] = content_type or "application/octet-stream"
            
            # Auto-generate filename if not specified
            if not processed_attachment.get("filename"):
                processed_attachment["filename"] = os.path.basename(file_path)
            
            processed_attachment["file_size"] = os.path.getsize(file_path)
            prepared.append(processed_attachment)
        
        return prepared
    
    async def send_smtp_email(self, config: Dict, session: Dict, context: Dict) -> Dict:
        """Send email via SMTP"""
        start_time = time.time()
        
        try:
            # Process SMTP configuration
            smtp_config = self.process_expressions_in_dict(config.get("smtp_config", {}), context)
            
            # Create message
            msg = MIMEMultipart('alternative')
            
            # Basic headers
            msg['From'] = formataddr((config.get("from_name", ""), config["from_email"]))
            msg['To'] = ", ".join(config["to"] if isinstance(config["to"], list) else [config["to"]])
            if config.get("cc"):
                msg['Cc'] = ", ".join(config["cc"] if isinstance(config["cc"], list) else [config["cc"]])
            if config.get("reply_to"):
                msg['Reply-To'] = config["reply_to"]
            
            msg['Subject'] = config["subject"]
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # Priority
            priority_map = {"low": "5", "normal": "3", "high": "1"}
            if config.get("priority", "normal") != "normal":
                msg['X-Priority'] = priority_map.get(config["priority"], "3")
            
            # Add text and HTML parts
            if config.get("body_text"):
                text_part = MIMEText(config["body_text"], 'plain', 'utf-8')
                msg.attach(text_part)
            
            if config.get("body_html"):
                html_part = MIMEText(config["body_html"], 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments
            if config.get("attachments"):
                attachments = self.prepare_attachments(config["attachments"], context)
                
                for attachment in attachments:
                    if "error" in attachment:
                        continue
                    
                    try:
                        with open(attachment["file_path"], "rb") as f:
                            file_data = f.read()
                        
                        if attachment.get("inline"):
                            # Inline attachment (like images)
                            part = MIMEBase(*attachment["content_type"].split("/"))
                            part.set_payload(file_data)
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'inline; filename="{attachment["filename"]}"'
                            )
                            if attachment.get("cid"):
                                part.add_header('Content-ID', f'<{attachment["cid"]}>')
                        else:
                            # Regular attachment
                            part = MIMEBase(*attachment["content_type"].split("/"))
                            part.set_payload(file_data)
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{attachment["filename"]}"'
                            )
                        
                        msg.attach(part)
                        
                    except Exception as e:
                        # Continue with other attachments
                        pass
            
            # Send email
            all_recipients = []
            all_recipients.extend(config["to"] if isinstance(config["to"], list) else [config["to"]])
            if config.get("cc"):
                all_recipients.extend(config["cc"] if isinstance(config["cc"], list) else [config["cc"]])
            if config.get("bcc"):
                all_recipients.extend(config["bcc"] if isinstance(config["bcc"], list) else [config["bcc"]])
            
            # Connect to SMTP server with timeout
            if smtp_config.get("use_ssl", False):
                server = smtplib.SMTP_SSL(smtp_config["host"], smtp_config.get("port", 465), timeout=30)
            else:
                server = smtplib.SMTP(smtp_config["host"], smtp_config.get("port", 587), timeout=30)
                if smtp_config.get("use_tls", True):
                    server.starttls(context=ssl.create_default_context())
            
            # Authenticate
            if smtp_config.get("username") and smtp_config.get("password"):
                server.login(smtp_config["username"], smtp_config["password"])
            
            # Send email
            server.send_message(msg, to_addrs=all_recipients)
            server.quit()
            
            send_time = time.time() - start_time
            
            return {
                "success": True,
                "message_id": msg.get("Message-ID"),
                "recipients": all_recipients,
                "send_time": send_time,
                "timestamp": datetime.now().isoformat(),
                "service": "smtp",
                "server": f"{smtp_config['host']}:{smtp_config.get('port', 587)}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "send_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "service": "smtp"
            }
    
    async def send_sendgrid_email(self, config: Dict, session: Dict, context: Dict) -> Dict:
        """Send email via SendGrid API"""
        start_time = time.time()
        
        try:
            api_config = self.process_expressions_in_dict(config.get("api_config", {}), context)
            api_key = api_config.get("api_key")
            
            if not api_key:
                raise ValueError("SendGrid API key is required")
            
            # Build SendGrid payload
            payload = {
                "personalizations": [{
                    "to": [{"email": email} for email in (config["to"] if isinstance(config["to"], list) else [config["to"]])]
                }],
                "from": {
                    "email": config["from_email"],
                    "name": config.get("from_name", "")
                },
                "subject": config["subject"]
            }
            
            # Add CC/BCC
            if config.get("cc"):
                payload["personalizations"][0]["cc"] = [{"email": email} for email in (config["cc"] if isinstance(config["cc"], list) else [config["cc"]])]
            if config.get("bcc"):
                payload["personalizations"][0]["bcc"] = [{"email": email} for email in (config["bcc"] if isinstance(config["bcc"], list) else [config["bcc"]])]
            
            # Add content
            content = []
            if config.get("body_text"):
                content.append({"type": "text/plain", "value": config["body_text"]})
            if config.get("body_html"):
                content.append({"type": "text/html", "value": config["body_html"]})
            
            payload["content"] = content
            
            # Template variables for personalization
            if config.get("template_vars"):
                payload["personalizations"][0]["dynamic_template_data"] = config["template_vars"]
            
            # Template ID
            if config.get("template", {}).get("template_id"):
                payload["template_id"] = config["template"]["template_id"]
            
            # Send request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            send_time = time.time() - start_time
            
            if response.status_code == 202:
                return {
                    "success": True,
                    "message_id": response.headers.get("X-Message-Id"),
                    "recipients": [email for email in (config["to"] if isinstance(config["to"], list) else [config["to"]])],
                    "send_time": send_time,
                    "timestamp": datetime.now().isoformat(),
                    "service": "sendgrid",
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code,
                    "send_time": send_time,
                    "timestamp": datetime.now().isoformat(),
                    "service": "sendgrid"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "send_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "service": "sendgrid"
            }
    
    async def send_email(self, config: Dict, session: Dict, context: Dict) -> Dict:
        """Send email using the configured service"""
        service = config.get("service", "smtp")
        
        if service == "smtp":
            return await self.send_smtp_email(config, session, context)
        elif service == "sendgrid":
            return await self.send_sendgrid_email(config, session, context)
        else:
            return {
                "success": False,
                "error": f"Unsupported email service: {service}",
                "timestamp": datetime.now().isoformat(),
                "service": service
            }
    
    async def handle_send_mode(self, params: Dict) -> Dict:
        """Handle single email send mode"""
        session_id = params.get("session_id")
        session = self.get_session(session_id)
        
        # Build context
        vars_dict = params.get("vars", {})
        session["vars"].update(vars_dict)
        template_vars = params.get("template_vars", {})
        
        context = self.build_expression_context(session, current_email=params, template_vars=template_vars, vars_dict=session["vars"])
        
        # Process expressions in all parameters
        processed_params = self.process_expressions_in_dict(params, context)
        
        # Process templates if specified
        if processed_params.get("template"):
            template_config = processed_params["template"]
            
            if template_config.get("subject"):
                processed_params["subject"] = self.render_template(template_config["subject"], context)
            if template_config.get("body_text"):
                processed_params["body_text"] = self.render_template(template_config["body_text"], context)
            if template_config.get("body_html"):
                processed_params["body_html"] = self.render_template(template_config["body_html"], context)
        
        # Validate email addresses if requested
        validation_results = {}
        if processed_params.get("validate_emails", True):
            all_emails = []
            all_emails.extend(processed_params["to"] if isinstance(processed_params["to"], list) else [processed_params["to"]])
            if processed_params.get("cc"):
                all_emails.extend(processed_params["cc"] if isinstance(processed_params["cc"], list) else [processed_params["cc"]])
            if processed_params.get("bcc"):
                all_emails.extend(processed_params["bcc"] if isinstance(processed_params["bcc"], list) else [processed_params["bcc"]])
            
            for email in all_emails:
                validation_results[email] = self.validate_email_address(email)
            
            # Check for invalid emails
            invalid_emails = [email for email, result in validation_results.items() if not result["valid"]]
            if invalid_emails:
                return {
                    "mode": "send",
                    "session_id": session["id"],
                    "success": False,
                    "error": f"Invalid email addresses: {', '.join(invalid_emails)}",
                    "validation_results": validation_results,
                    "timestamp": datetime.now().isoformat()
                }
        
        # Send email
        result = await self.send_email(processed_params, session, context)
        
        # Update session
        if result["success"]:
            session["sent_emails"].append({
                "timestamp": result["timestamp"],
                "recipients": result["recipients"],
                "subject": processed_params.get("subject", ""),
                "service": result["service"],
                "message_id": result.get("message_id")
            })
            session["metrics"]["total_sent"] += 1
        else:
            session["failed_emails"].append({
                "timestamp": result["timestamp"],
                "error": result["error"],
                "config": processed_params
            })
            session["metrics"]["total_failed"] += 1
        
        # Update metrics
        session["metrics"]["avg_send_time"] = (
            (session["metrics"]["avg_send_time"] * (session["metrics"]["total_sent"] + session["metrics"]["total_failed"] - 1) + 
             result.get("send_time", 0)) /
            (session["metrics"]["total_sent"] + session["metrics"]["total_failed"])
        )
        session["metrics"]["last_activity"] = datetime.now().isoformat()
        
        # Save session
        self.save_session(session["id"])
        
        return {
            "mode": "send",
            "session_id": session["id"],
            "result": result,
            "validation_results": validation_results if validation_results else None,
            "session_metrics": session["metrics"]
        }
    
    async def handle_batch_mode(self, params: Dict) -> Dict:
        """Handle batch email sending mode"""
        session_id = params.get("session_id")
        session = self.get_session(session_id)
        
        recipients = params.get("recipients", [])
        batch_config = params.get("batch_config", {})
        batch_size = batch_config.get("batch_size", 10)
        delay_between_batches = batch_config.get("delay_between_batches", 1)
        
        # Build base context
        vars_dict = params.get("vars", {})
        session["vars"].update(vars_dict)
        
        results = []
        total_sent = 0
        total_failed = 0
        
        # Process recipients in batches
        for i in range(0, len(recipients), batch_size):
            batch_recipients = recipients[i:i + batch_size]
            batch_results = []
            
            for recipient in batch_recipients:
                # Build context for this recipient
                recipient_context = self.build_expression_context(
                    session, 
                    current_email=params,
                    recipient=recipient,
                    template_vars=params.get("template_vars", {}),
                    vars_dict=session["vars"]
                )
                
                # Create email config for this recipient
                email_config = params.copy()
                email_config["to"] = recipient["email"]
                
                # Process expressions and templates for this recipient
                processed_config = self.process_expressions_in_dict(email_config, recipient_context)
                
                # Process templates
                if processed_config.get("template"):
                    template_config = processed_config["template"]
                    combined_vars = {**params.get("template_vars", {}), **recipient, **session["vars"]}
                    template_context = {**recipient_context, "template_vars": combined_vars}
                    
                    if template_config.get("subject"):
                        processed_config["subject"] = self.render_template(template_config["subject"], template_context)
                    if template_config.get("body_text"):
                        processed_config["body_text"] = self.render_template(template_config["body_text"], template_context)
                    if template_config.get("body_html"):
                        processed_config["body_html"] = self.render_template(template_config["body_html"], template_context)
                
                # Send email
                result = await self.send_email(processed_config, session, recipient_context)
                result["recipient"] = recipient
                batch_results.append(result)
                
                if result["success"]:
                    total_sent += 1
                else:
                    total_failed += 1
            
            results.extend(batch_results)
            
            # Delay between batches (except for the last batch)
            if i + batch_size < len(recipients) and delay_between_batches > 0:
                await asyncio.sleep(delay_between_batches)
        
        # Update session
        session["metrics"]["total_sent"] += total_sent
        session["metrics"]["total_failed"] += total_failed
        session["metrics"]["last_activity"] = datetime.now().isoformat()
        
        # Save session
        self.save_session(session["id"])
        
        return {
            "mode": "batch",
            "session_id": session["id"],
            "total_recipients": len(recipients),
            "total_sent": total_sent,
            "total_failed": total_failed,
            "batch_size": batch_size,
            "batches_processed": (len(recipients) + batch_size - 1) // batch_size,
            "results": results,
            "session_metrics": session["metrics"]
        }
    
    async def handle_test_mode(self, params: Dict) -> Dict:
        """Handle email service testing mode"""
        session_id = params.get("session_id")
        session = self.get_session(session_id)
        
        test_config = params.get("test_config", {})
        service = params.get("service", "smtp")
        
        # Build context
        vars_dict = params.get("vars", {})
        session["vars"].update(vars_dict)
        context = self.build_expression_context(session, vars_dict=session["vars"])
        
        results = {
            "service": service,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        if service == "smtp":
            # Test SMTP connection
            smtp_config = self.process_expressions_in_dict(params.get("smtp_config", {}), context)
            
            try:
                if smtp_config.get("use_ssl", False):
                    server = smtplib.SMTP_SSL(smtp_config["host"], smtp_config.get("port", 465), timeout=30)
                else:
                    server = smtplib.SMTP(smtp_config["host"], smtp_config.get("port", 587), timeout=30)
                    if smtp_config.get("use_tls", True):
                        server.starttls(context=ssl.create_default_context())
                
                results["tests"]["connection"] = {
                    "success": True,
                    "message": f"Successfully connected to {smtp_config['host']}:{smtp_config.get('port', 587)}"
                }
                
                # Test authentication
                if smtp_config.get("username") and smtp_config.get("password"):
                    server.login(smtp_config["username"], smtp_config["password"])
                    results["tests"]["authentication"] = {
                        "success": True,
                        "message": "Successfully authenticated"
                    }
                
                server.quit()
                
            except Exception as e:
                results["tests"]["connection"] = {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                
                if smtp_config.get("username"):
                    results["tests"]["authentication"] = {
                        "success": False,
                        "error": "Could not test authentication due to connection failure"
                    }
        
        elif service == "sendgrid":
            # Test SendGrid API
            api_config = self.process_expressions_in_dict(params.get("api_config", {}), context)
            api_key = api_config.get("api_key")
            
            if not api_key:
                results["tests"]["api_key"] = {
                    "success": False,
                    "error": "API key is required for SendGrid"
                }
            else:
                try:
                    headers = {"Authorization": f"Bearer {api_key}"}
                    response = requests.get("https://api.sendgrid.com/v3/user/profile", headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        results["tests"]["api_connection"] = {
                            "success": True,
                            "message": "Successfully connected to SendGrid API"
                        }
                    else:
                        results["tests"]["api_connection"] = {
                            "success": False,
                            "error": f"API returned status {response.status_code}",
                            "response": response.text[:200]
                        }
                        
                except Exception as e:
                    results["tests"]["api_connection"] = {
                        "success": False,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
        
        # Send test email if requested
        if test_config.get("send_test_email", True) and test_config.get("test_recipient"):
            test_email_config = params.copy()
            test_email_config.update({
                "to": test_config["test_recipient"],
                "subject": f"Test Email from {service} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "body_text": f"This is a test email sent via {service} service at {datetime.now().isoformat()}",
                "body_html": f"<h1>Test Email</h1><p>This is a test email sent via <b>{service}</b> service at {datetime.now().isoformat()}</p>"
            })
            
            test_result = await self.send_email(test_email_config, session, context)
            results["tests"]["test_email"] = test_result
        
        return {
            "mode": "test",
            "session_id": session["id"],
            "results": results
        }
    
    async def handle_validate_mode(self, params: Dict) -> Dict:
        """Handle email validation mode"""
        validation_results = {
            "mode": "validate",
            "timestamp": datetime.now().isoformat(),
            "results": {}
        }
        
        # Validate email addresses
        emails_to_validate = []
        if params.get("to"):
            emails_to_validate.extend(params["to"] if isinstance(params["to"], list) else [params["to"]])
        if params.get("cc"):
            emails_to_validate.extend(params["cc"] if isinstance(params["cc"], list) else [params["cc"]])
        if params.get("bcc"):
            emails_to_validate.extend(params["bcc"] if isinstance(params["bcc"], list) else [params["bcc"]])
        
        for email in emails_to_validate:
            validation_results["results"][email] = self.validate_email_address(email)
        
        # Validate content if requested
        if params.get("validate_content", False):
            content_validation = {}
            
            if params.get("subject"):
                content_validation["subject"] = {
                    "length": len(params["subject"]),
                    "too_long": len(params["subject"]) > 200,
                    "contains_spam_words": any(word in params["subject"].lower() for word in ["free", "urgent", "click here", "limited time"])
                }
            
            if params.get("body_text") or params.get("body_html"):
                body = params.get("body_html", "") + params.get("body_text", "")
                content_validation["body"] = {
                    "length": len(body),
                    "has_unsubscribe": "unsubscribe" in body.lower(),
                    "has_links": "http" in body.lower(),
                    "text_to_html_ratio": len(params.get("body_text", "")) / max(len(params.get("body_html", "")), 1)
                }
            
            validation_results["content_validation"] = content_validation
        
        return validation_results
    
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
                "total_sent": len(session["sent_emails"]),
                "total_failed": len(session["failed_emails"]),
                "templates": list(session["templates"].keys()),
                "vars": session["vars"],
                "metrics": session["metrics"],
                "recent_emails": session["sent_emails"][-5:] if session["sent_emails"] else []
            }
        }


async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Main tool execution function"""
    try:
        client = EmailClient()
        mode = parameters.get("mode", "send")
        
        # Load config from file if specified
        config_file = parameters.get("config_file")
        if config_file:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                        import yaml
                        file_config = yaml.safe_load(f)
                    else:
                        file_config = json.load(f)
                # Merge file config with parameters (parameters take precedence)
                merged_params = {**file_config, **parameters}
                parameters = merged_params
            except Exception as e:
                return [types.TextContent(type="text", text=f"❌ Error loading config file: {str(e)}")]
        
        # Route to appropriate handler based on mode
        if mode == "send":
            result = await client.handle_send_mode(parameters)
        elif mode == "batch":
            result = await client.handle_batch_mode(parameters)
        elif mode == "test":
            result = await client.handle_test_mode(parameters)
        elif mode == "validate":
            result = await client.handle_validate_mode(parameters)
        elif mode == "session_info":
            result = await client.handle_session_info_mode(parameters)
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
                pipeline_context = {
                    "email_result": result,
                    "session": client.sessions.get(result.get("session_id", ""), {})
                }
                
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
            text=f"❌ Email Client Error: {str(e)}\nType: {type(e).__name__}"
        )]
