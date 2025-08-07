import os
import imaplib
import email
import json
import ssl
from datetime import datetime, timedelta
from typing import Dict, Any, List
import mcp.types as types
from email.header import decode_header
import base64
from dotenv import load_dotenv

# Load environment variables from project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)


def get_email_config():
    """Get email configuration from environment variables."""
    gmail_email = os.getenv('GMAIL_EMAIL')
    gmail_password = os.getenv('GMAIL_PASSWORD')
    
    # Простая проверка - если credentials отсутствуют, вернем информативное сообщение
    if not gmail_email:
        print(f"❌ GMAIL_EMAIL not found. env_path: {env_path}")
        print(f"❌ Project root: {project_root}")
        print(f"❌ .env exists: {os.path.exists(env_path)}")
    
    return {
        'gmail': {
            'email': gmail_email,
            'password': gmail_password,
            'server': 'imap.gmail.com',
            'port': 993
        },
        'mailru_1': {
            'email': os.getenv('MAILRU_EMAIL_1'),
            'password': os.getenv('MAILRU_PASSWORD_1'),
            'server': 'imap.mail.ru',
            'port': 993
        },
        'mailru_2': {
            'email': os.getenv('MAILRU_EMAIL_2'),
            'password': os.getenv('MAILRU_PASSWORD_2'),
            'server': 'imap.mail.ru',
            'port': 993
        }
    }


def decode_mime_words(s):
    """Decode MIME encoded words in email headers."""
    if s is None:
        return ""
    decoded = decode_header(s)
    result = ""
    for text, encoding in decoded:
        if isinstance(text, bytes):
            try:
                result += text.decode(encoding or 'utf-8')
            except (UnicodeDecodeError, LookupError):
                result += text.decode('utf-8', errors='ignore')
        else:
            result += text
    return result


def get_email_body(msg):
    """Extract email body from message."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body += payload.decode(charset, errors='ignore')
                except Exception:
                    pass
            elif content_type == "text/html" and "attachment" not in content_disposition and not body:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body += payload.decode(charset, errors='ignore')
                except Exception:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='ignore')
        except Exception:
            pass
    
    return body.strip()


def extract_unread_emails(mailbox_type: str, days_back: int = 7) -> Dict[str, Any]:
    """
    Extract unread emails from specified mailbox for the given period.
    
    Args:
        mailbox_type (str): Type of mailbox ('gmail', 'mailru_1', 'mailru_2')
        days_back (int): Number of days to look back for emails
    
    Returns:
        Dict[str, Any]: Result containing success status and extracted emails
    """
    try:
        email_config = get_email_config()
        
        if mailbox_type not in email_config:
            return {
                "success": False,
                "message": f"Unknown mailbox type: {mailbox_type}",
                "emails": []
            }
        
        mailbox_config = email_config[mailbox_type]
        
        if not mailbox_config['email'] or not mailbox_config['password']:
            debug_info = f"email='{mailbox_config.get('email')}', password_exists={bool(mailbox_config.get('password'))}, env_path={env_path}"
            return {
                "success": False,
                "message": f"Missing credentials for {mailbox_type}: {debug_info}",
                "emails": []
            }
        
        # Create SSL context with relaxed verification for development
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Connect to IMAP server
        with imaplib.IMAP4_SSL(mailbox_config['server'], mailbox_config['port'], ssl_context=context) as mail:
            # Login
            mail.login(mailbox_config['email'], mailbox_config['password'])
            
            # Select INBOX
            mail.select('INBOX')
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Search for unread emails in date range
            date_str = start_date.strftime("%d-%b-%Y")
            search_criteria = f'(UNSEEN SINCE "{date_str}")'
            
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK':
                return {
                    "success": False,
                    "message": "Failed to search emails",
                    "emails": []
                }
            
            email_ids = messages[0].split()
            extracted_emails = []
            
            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    
                    if status == 'OK':
                        # Parse email
                        raw_email = msg_data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        
                        # Extract email data
                        email_data = {
                            "id": email_id.decode(),
                            "subject": decode_mime_words(msg["Subject"]),
                            "from": decode_mime_words(msg["From"]),
                            "to": decode_mime_words(msg["To"]),
                            "date": msg["Date"],
                            "body": get_email_body(msg),
                            "mailbox": mailbox_type,
                            "extracted_at": datetime.now().isoformat()
                        }
                        
                        extracted_emails.append(email_data)
                        
                except Exception as e:
                    print(f"Error processing email {email_id}: {str(e)}")
                    continue
            
            return {
                "success": True,
                "message": f"Successfully extracted {len(extracted_emails)} unread emails from {mailbox_type}",
                "mailbox": mailbox_type,
                "period_days": days_back,
                "total_emails": len(extracted_emails),
                "emails": extracted_emails
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error connecting to {mailbox_type}: {str(e)}",
            "emails": []
        }


def save_emails_to_json(emails_data: Dict[str, Any], custom_filename: str = None) -> str:
    """Save extracted emails to JSON file."""
    try:
        # Create emails directory if it doesn't exist
        base_dir = "/Users/evgeniy_admin/Documents/Automation project/copilot-mcp-langchain"
        emails_dir = os.path.join(base_dir, "extracted_emails")
        os.makedirs(emails_dir, exist_ok=True)
        
        # Generate filename
        if custom_filename:
            filename = f"{custom_filename}.json"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mailbox = emails_data.get('mailbox', 'unknown')
            filename = f"emails_{mailbox}_{timestamp}.json"
        
        filepath = os.path.join(emails_dir, filename)
        
        # Save to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(emails_data, f, ensure_ascii=False, indent=2)
        
        return filepath
        
    except Exception as e:
        raise Exception(f"Error saving emails to JSON: {str(e)}")


def tool_lng_email_extractor(mailbox_type: str, days_back: int = 7, save_to_file: bool = True, custom_filename: str = None) -> str:
    """
    MCP tool wrapper for email extraction.
    
    Args:
        mailbox_type (str): Type of mailbox ('gmail', 'mailru_1', 'mailru_2')
        days_back (int): Number of days to look back for emails (default: 7)
        save_to_file (bool): Whether to save emails to JSON file (default: True)
        custom_filename (str): Custom filename for JSON file (optional)
    
    Returns:
        str: Formatted result message
    """
    result = extract_unread_emails(mailbox_type, days_back)
    
    if result["success"]:
        message = f"✅ {result['message']}\n"
        message += f"📧 Mailbox: {result['mailbox']}\n"
        message += f"📅 Period: Last {result['period_days']} days\n"
        message += f"📊 Total emails: {result['total_emails']}\n\n"
        
        if save_to_file and result['emails']:
            try:
                filepath = save_emails_to_json(result, custom_filename)
                message += f"💾 Emails saved to: {filepath}\n\n"
            except Exception as e:
                message += f"⚠️ Error saving to file: {str(e)}\n\n"
        
        if result["emails"]:
            message += "📬 Recent emails:\n"
            for i, email_data in enumerate(result["emails"][:5], 1):  # Show first 5 emails
                message += f"  {i}. From: {email_data['from']}\n"
                message += f"     Subject: {email_data['subject']}\n"
                message += f"     Date: {email_data['date']}\n"
                message += f"     Body preview: {email_data['body'][:100]}...\n\n"
            
            if len(result["emails"]) > 5:
                message += f"     ... and {len(result['emails']) - 5} more emails\n"
        
        return message
    else:
        return f"❌ {result['message']}"


# Tool metadata for MCP registration
TOOL_NAME = "lng_email_extractor"
TOOL_DESCRIPTION = "Extracts unread emails from mailboxes and saves them as JSON files locally"


# MCP required functions
async def tool_info():
    """Return tool information for MCP."""
    return {
        "description": f"""{TOOL_DESCRIPTION}

**Parameters:**
- `mailbox_type` (string, required): Type of mailbox ('gmail', 'mailru_1', 'mailru_2')
- `days_back` (integer, optional): Number of days to look back for emails (default: 7)
- `save_to_file` (boolean, optional): Whether to save emails to JSON file (default: true)
- `custom_filename` (string, optional): Custom filename for JSON file

**Example Usage:**
- Extract emails from Gmail for last 7 days: mailbox_type="gmail", days_back=7
- Extract from Mail.ru account 1 for last 3 days: mailbox_type="mailru_1", days_back=3
- Save with custom filename: custom_filename="my_emails"

**Email Storage:**
- JSON files are stored in 'extracted_emails' folder
- Files should be reviewed and deleted weekly as agreed
- Each file contains metadata and email content

This tool is useful for email management and archiving unread messages.""",
        "schema": {
            "type": "object",
            "properties": {
                "mailbox_type": {
                    "type": "string",
                    "enum": ["gmail", "mailru_1", "mailru_2"],
                    "description": "Type of mailbox to extract emails from"
                },
                "days_back": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 30,
                    "default": 7,
                    "description": "Number of days to look back for emails"
                },
                "save_to_file": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to save emails to JSON file"
                },
                "custom_filename": {
                    "type": "string",
                    "description": "Custom filename for JSON file (optional)"
                }
            },
            "required": ["mailbox_type"]
        }
    }


async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Run the tool with provided parameters."""
    try:
        mailbox_type = parameters.get("mailbox_type")
        days_back = parameters.get("days_back", 7)
        save_to_file = parameters.get("save_to_file", True)
        custom_filename = parameters.get("custom_filename")
        
        if not mailbox_type:
            return [types.TextContent(type="text", text='{"error": "mailbox_type is required"}')]
        
        result = tool_lng_email_extractor(mailbox_type, days_back, save_to_file, custom_filename)
        return [types.TextContent(type="text", text=result)]
        
    except Exception as e:
        error_result = f'{{"error": "Error extracting emails: {str(e)}"}}'
        return [types.TextContent(type="text", text=error_result)]


if __name__ == "__main__":
    # Test the tool
    print("Testing Email Extractor Tool")
    result = tool_lng_email_extractor("gmail", 3, True, "test_emails")
    print(result)
