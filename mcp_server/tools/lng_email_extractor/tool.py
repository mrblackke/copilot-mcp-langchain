import os
from datetime import datetime, timedelta
import ssl
import mcp.types as types
import yaml

# Import modules
from .mailbox import MailboxConnector
from .extractor import extract_email_fields
from .saver import save_emails_to_json
from dotenv import load_dotenv

# Load environment variables from project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

# Get current module directory
module_dir = os.path.dirname(os.path.abspath(__file__))
settings_file = os.path.join(module_dir, 'settings.yaml')

# Default configuration
DEFAULT_SETTINGS = {
    'subject_keywords': [],
    'sender_keywords': [],
    'defaults': {
        'days_back': 7,
        'max_emails': 50,
        'only_unread': True,
        'use_subject_keywords': False,
        'use_sender_keywords': False
    }
}

# Load settings
def load_settings():
    """Load settings from YAML file"""
    try:
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            print(f"Settings file not found: {settings_file}")
            return DEFAULT_SETTINGS
    except Exception as e:
        print(f"Error loading settings: {e}")
        return DEFAULT_SETTINGS
        
SETTINGS = load_settings()

def get_email_config():
    gmail_email = os.getenv('GMAIL_EMAIL')
    gmail_password = os.getenv('GMAIL_PASSWORD')
    return {
        'gmail': {
            'email': gmail_email,
            'password': gmail_password,
            'provider': 'gmail'
        },
        'mailru_1': {
            'email': os.getenv('MAILRU_EMAIL_1'),
            'password': os.getenv('MAILRU_PASSWORD_1'),
            'provider': 'mailru'
        },
        'mailru_2': {
            'email': os.getenv('MAILRU_EMAIL_2'),
            'password': os.getenv('MAILRU_PASSWORD_2'),
            'provider': 'mailru'
        }
    }

def extract_unread_emails(mailbox_type: str, days_back: int = 7, max_emails: int = None,
                     only_unread: bool = True, subject_filter: str = None, from_filter: str = None):
    """
    Extract emails from specified mailbox with filtering options.
    
    Args:
        mailbox_type (str): Type of mailbox ('gmail', 'mailru_1', 'mailru_2')
        days_back (int): Number of days to look back for emails
        max_emails (int): Maximum number of emails to extract (None for all)
        only_unread (bool): Whether to fetch only unread emails
        subject_filter (str): Filter emails by subject containing this string
        from_filter (str): Filter emails by sender containing this string
    
    Returns:
        Dict with extraction results
    """
    email_config = get_email_config()
    if mailbox_type not in email_config:
        return {
            "success": False,
            "message": f"Unknown mailbox type: {mailbox_type}",
            "emails": []
        }
    mailbox_cfg = email_config[mailbox_type]
    if not mailbox_cfg['email'] or not mailbox_cfg['password']:
        return {
            "success": False,
            "message": f"Missing credentials for {mailbox_type}",
            "emails": []
        }
    connector = MailboxConnector(mailbox_cfg['provider'], mailbox_cfg['email'], mailbox_cfg['password'])
    try:
        conn = connector.connect()
        connector.select_mailbox('INBOX')
        
        # Get email IDs with filtering
        email_ids = connector.fetch_email_ids(
            days_back=days_back,
            only_unread=only_unread,
            max_emails=max_emails
        )
        
        if not email_ids:
            return {
                "success": True,
                "message": f"No emails found matching criteria in {mailbox_type}",
                "mailbox": mailbox_type,
                "period_days": days_back,
                "total_emails": 0,
                "emails": []
            }
        
        emails = []
        import email
        
        # Process emails
        for eid in email_ids:
            try:
                email_data = None
                raw_data = connector.fetch_email_data(eid)
                if raw_data:
                    msg = email.message_from_bytes(raw_data)
                    email_data = extract_email_fields(msg, mailbox_cfg['email'])
                    email_data['id'] = eid.decode()
                    
                    # Apply additional filtering if needed
                    include_email = True
                    
                    # Process subject filter - can be single string or comma/semicolon separated list
                    if subject_filter:
                        subject_match = False
                        # Split by comma or semicolon and strip whitespace
                        if isinstance(subject_filter, str):
                            keywords = [kw.strip() for kw in subject_filter.replace(';', ',').split(',')]
                            email_subject = email_data.get('subject', '').lower()
                            
                            # Check if any keyword matches
                            for keyword in keywords:
                                if keyword and keyword.lower() in email_subject:
                                    subject_match = True
                                    break
                            
                            if not subject_match:
                                include_email = False
                    
                    # Process from filter - can be single string or comma/semicolon separated list
                    if from_filter:
                        from_match = False
                        # Split by comma or semicolon and strip whitespace
                        if isinstance(from_filter, str):
                            keywords = [kw.strip() for kw in from_filter.replace(';', ',').split(',')]
                            email_from = email_data.get('from', '').lower()
                            
                            # Check if any keyword matches
                            for keyword in keywords:
                                if keyword and keyword.lower() in email_from:
                                    from_match = True
                                    break
                            
                            if not from_match:
                                include_email = False
                        
                    if include_email:
                        emails.append(email_data)
                        
                    # Apply max limit again after filtering
                    if max_emails and len(emails) >= max_emails:
                        break
                    
            except Exception as e:
                print(f"Error processing email {eid}: {e}")
                continue
                
        connector.logout()
        return {
            "success": True,
            "message": f"Successfully extracted {len(emails)} emails from {mailbox_type}",
            "mailbox": mailbox_type,
            "period_days": days_back,
            "filters_applied": {
                "days_back": days_back,
                "only_unread": only_unread,
                "max_emails": max_emails,
                "subject_filter": subject_filter,
                "from_filter": from_filter
            },
            "total_emails": len(emails),
            "emails": emails
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error connecting to {mailbox_type}: {str(e)}",
            "emails": []
        }

def tool_lng_email_extractor(mailbox_type: str, days_back: int = None, save_to_file: bool = True, 
                       custom_filename: str = None, max_emails: int = None, only_unread: bool = None,
                       subject_filter: str = None, from_filter: str = None, 
                       use_config_keywords: bool = None) -> str:
    """
    MCP tool wrapper for email extraction with filtering.
    
    Args:
        mailbox_type (str): Type of mailbox ('gmail', 'mailru_1', 'mailru_2')
        days_back (int): Number of days to look back for emails
        save_to_file (bool): Whether to save results to file
        custom_filename (str): Custom filename for saved results
        max_emails (int): Maximum number of emails to extract
        only_unread (bool): Whether to fetch only unread emails
        subject_filter (str): Filter emails by subject containing this string
        from_filter (str): Filter emails by sender containing this string
        use_config_keywords (bool): Whether to use keywords from config file
        
    Returns:
        Formatted result message
    """
    # Use defaults from settings if not specified
    if days_back is None:
        days_back = SETTINGS.get('defaults', {}).get('days_back', 7)
        
    if max_emails is None:
        max_emails = SETTINGS.get('defaults', {}).get('max_emails', None)
        
    if only_unread is None:
        only_unread = SETTINGS.get('defaults', {}).get('only_unread', True)
    
    # Use settings keywords if enabled and no explicit filter provided
    if use_config_keywords is None:
        use_config_keywords = SETTINGS.get('defaults', {}).get('use_subject_keywords', False)
        
    final_subject_filter = subject_filter
    if not subject_filter and use_config_keywords:
        # Convert list of keywords to comma-separated string
        keywords = SETTINGS.get('subject_keywords', [])
        if keywords:
            final_subject_filter = ", ".join(keywords)
    
    final_from_filter = from_filter
    if not from_filter and use_config_keywords and SETTINGS.get('defaults', {}).get('use_sender_keywords', False):
        # Convert list of sender keywords to comma-separated string
        keywords = SETTINGS.get('sender_keywords', [])
        if keywords:
            final_from_filter = ", ".join(keywords)
    
    result = extract_unread_emails(
        mailbox_type, 
        days_back=days_back,
        max_emails=max_emails,
        only_unread=only_unread,
        subject_filter=final_subject_filter,
        from_filter=final_from_filter
    )
    
    if result["success"]:
        message = f"✅ {result['message']}\n"
        message += f"📧 Mailbox: {result['mailbox']}\n"
        message += f"📅 Period: Last {result['period_days']} days\n"
        
        # Add filter info if applied
        filters = []
        if only_unread:
            filters.append("только непрочитанные")
        if max_emails:
            filters.append(f"максимум {max_emails}")
        if subject_filter:
            if ',' in subject_filter or ';' in subject_filter:
                keywords = [kw.strip() for kw in subject_filter.replace(';', ',').split(',') if kw.strip()]
                filters.append(f"тема содержит любое из: {', '.join([f'"{kw}"' for kw in keywords])}")
            else:
                filters.append(f"тема содержит '{subject_filter}'")
                
        if from_filter:
            if ',' in from_filter or ';' in from_filter:
                keywords = [kw.strip() for kw in from_filter.replace(';', ',').split(',') if kw.strip()]
                filters.append(f"отправитель содержит любое из: {', '.join([f'"{kw}"' for kw in keywords])}")
            else:
                filters.append(f"отправитель содержит '{from_filter}'")
            
        if filters:
            message += f"🔍 Фильтры: {'; '.join(filters)}\n"
            
        message += f"📊 Total emails: {result['total_emails']}\n\n"
        if save_to_file and result['emails']:
            try:
                base_dir = project_root
                emails_dir = os.path.join(base_dir, "extracted_emails")
                filename = custom_filename if custom_filename else None
                filepath = save_emails_to_json(result, emails_dir, filename or f"emails_{result['mailbox']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                message += f"💾 Emails saved to: {filepath}\n\n"
            except Exception as e:
                message += f"⚠️ Error saving to file: {str(e)}\n\n"
        if result["emails"]:
            message += "📬 Recent emails:\n"
            for i, email_data in enumerate(result["emails"][:5], 1):
                message += f"  {i}. From: {email_data['from']}\n"
                message += f"     Subject: {email_data['subject']}\n"
                message += f"     Date: {email_data['date']}\n"
                message += f"     Body preview: {email_data['body'][:100]}...\n\n"
            if len(result["emails"]) > 5:
                message += f"     ... and {len(result['emails']) - 5} more emails\n"
        return message
    else:
        return f"❌ {result['message']}"

TOOL_NAME = "lng_email_extractor"
TOOL_DESCRIPTION = "Extracts unread emails from mailboxes and saves them as JSON files locally"

async def tool_info():
    return {
        "description": f"""{TOOL_DESCRIPTION}

**Parameters:**
- `mailbox_type` (string, required): Type of mailbox ('gmail', 'mailru_1', 'mailru_2')
- `days_back` (integer, optional): Number of days to look back for emails (default: from settings)
- `save_to_file` (boolean, optional): Whether to save emails to JSON file (default: true)
- `custom_filename` (string, optional): Custom filename for JSON file
- `max_emails` (integer, optional): Maximum number of emails to extract (default: from settings)
- `only_unread` (boolean, optional): Whether to fetch only unread emails (default: from settings)
- `subject_filter` (string, optional): Filter emails by subject containing any of these keywords (comma or semicolon separated list)
- `from_filter` (string, optional): Filter emails by sender containing any of these keywords (comma or semicolon separated list)
- `use_config_keywords` (boolean, optional): Whether to use keywords from settings.yaml file (default: from settings)

**Example Usage:**
- Extract emails from Gmail for last 7 days: mailbox_type="gmail", days_back=7
- Extract with limit: mailbox_type="gmail", max_emails=10
- Filter by subject: mailbox_type="gmail", subject_filter="Invoice"
- Filter by multiple subjects: mailbox_type="gmail", subject_filter="Order Confirmation, Your cult beauty order, Twoje zamówienie"
- Filter by sender: mailbox_type="gmail", from_filter="amazon"
- Filter by multiple senders: mailbox_type="gmail", from_filter="amazon, ebay, shop"
- Multiple filters: mailbox_type="gmail", subject_filter="Order, Invoice", from_filter="shop, store", max_emails=5
- Use keywords from settings.yaml: mailbox_type="gmail", use_config_keywords=true

**Email Storage:**
- JSON files are stored in 'extracted_emails' folder
- Files should be reviewed and deleted weekly as agreed
- Each file contains metadata and email content

This tool is useful for email management and filtering important messages.""",
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
                },
                "max_emails": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Maximum number of emails to extract"
                },
                "only_unread": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to fetch only unread emails"
                },
                "subject_filter": {
                    "type": "string",
                    "description": "Filter emails by subject containing any of these keywords (comma or semicolon separated list)"
                },
                "from_filter": {
                    "type": "string",
                    "description": "Filter emails by sender containing any of these keywords (comma or semicolon separated list)"
                },
                "use_config_keywords": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to use keywords from config.yaml file"
                }
            },
            "required": ["mailbox_type"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    try:
        # Get parameters with defaults
        mailbox_type = parameters.get("mailbox_type")
        days_back = parameters.get("days_back", 7)
        save_to_file = parameters.get("save_to_file", True)
        custom_filename = parameters.get("custom_filename")
        max_emails = parameters.get("max_emails")
        only_unread = parameters.get("only_unread", True)
        subject_filter = parameters.get("subject_filter")
        from_filter = parameters.get("from_filter")
        use_config_keywords = parameters.get("use_config_keywords")
        
        if not mailbox_type:
            return [types.TextContent(type="text", text='{"error": "mailbox_type is required"}')]
        
        # Call tool with all parameters
        result = tool_lng_email_extractor(
            mailbox_type, 
            days_back=days_back, 
            save_to_file=save_to_file, 
            custom_filename=custom_filename,
            max_emails=max_emails,
            only_unread=only_unread,
            subject_filter=subject_filter,
            from_filter=from_filter,
            use_config_keywords=use_config_keywords
        )
        
        return [types.TextContent(type="text", text=result)]
    except Exception as e:
        error_result = f'{{"error": "Error extracting emails: {str(e)}"}}'
        return [types.TextContent(type="text", text=error_result)]

if __name__ == "__main__":
    print("Testing Email Extractor Tool")
    result = tool_lng_email_extractor("gmail", 3, True, "test_emails")
    print(result)
