# Email Client Tool - Universal Email Swiss Army Knife

Universal email client tool with support for SMTP servers, API services, templates, attachments, and batch processing.

## Features

- **Multiple Protocols**: SMTP (Gmail, Outlook, custom servers) and API services (SendGrid, Mailgun, SES)
- **Advanced Authentication**: Basic auth, OAuth, API keys, app passwords
- **Rich Content**: HTML emails, plain text, mixed content with inline images
- **Smart Attachments**: Multiple files, inline images, automatic MIME type detection
- **Template Engine**: Jinja2 templates with variables, conditionals, loops
- **Batch Operations**: Mass mailing with personalization and rate limiting
- **Expression System**: Dynamic content with environment variables and context
- **State Management**: Session persistence, delivery tracking, retry logic
- **Validation**: Email address validation, content checks, deliverability tests

## Operation Modes

### `send` - Send Single Email
Send individual emails with full configuration support.

**Example:**
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
  "from_email": "{! env.GMAIL_USER !}",
  "from_name": "Your App",
  "to": "recipient@example.com",
  "subject": "Test Email - {! datetime.now().strftime('%Y-%m-%d') !}",
  "body_text": "Hello, this is a test email!",
  "body_html": "<h1>Hello!</h1><p>This is a <b>test</b> email!</p>"
}
```

### `batch` - Mass Email Sending
Send personalized emails to multiple recipients with rate limiting and batching.

**Example:**
```json
{
  "mode": "batch",
  "service": "smtp",
  "smtp_config": {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "{! env.GMAIL_USER !}",
    "password": "{! env.GMAIL_APP_PASSWORD !}"
  },
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
    "delay_between_batches": 10
  }
}
```

### `template` - Template-based Email Generation
Use Jinja2 templates for dynamic content generation.

**Example:**
```json
{
  "mode": "template",
  "template": {
    "subject": "Order Confirmation #{{order_id}}",
    "body_html": "<h1>Thank you {{customer_name}}!</h1><p>Your order #{{order_id}} for {{amount}} has been confirmed.</p>"
  },
  "template_vars": {
    "customer_name": "John Smith",
    "order_id": "12345",
    "amount": "$99.99"
  }
}
```

### `validate` - Email Address and Content Validation
Validate email addresses and check content for spam indicators.

**Example:**
```json
{
  "mode": "validate",
  "to": ["valid@example.com", "invalid-format", "user+tag@domain.co.uk"],
  "validate_content": true,
  "subject": "Test Subject",
  "body_text": "Email content to validate"
}
```

### `test` - Connection Testing
Test email server connections and authentication.

**Example:**
```json
{
  "mode": "test",
  "service": "smtp",
  "smtp_config": {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "{! env.GMAIL_USER !}",
    "password": "{! env.GMAIL_APP_PASSWORD !}"
  },
  "test_config": {
    "connection_only": true,
    "send_test_email": false
  }
}
```

### `session_info` - Session Information
Get information about email session and statistics.

**Example:**
```json
{
  "mode": "session_info",
  "session_id": "my_email_session"
}
```

## Email Services Support

### SMTP Servers
- **Gmail**: `smtp.gmail.com:587` (TLS)
- **Outlook/Hotmail**: `smtp-mail.outlook.com:587` (TLS)
- **Yahoo**: `smtp.mail.yahoo.com:587` (TLS)
- **Custom SMTP**: Any SMTP server with authentication

### API Services
- **SendGrid**: HTTP API with templates and personalization
- **Mailgun**: HTTP API with batch sending
- **Amazon SES**: HTTP API with high deliverability
- **Custom API**: Generic HTTP API support

## Configuration Options

### SMTP Configuration
```json
{
  "smtp_config": {
    "host": "smtp.example.com",
    "port": 587,
    "username": "{! env.SMTP_USER !}",
    "password": "{! env.SMTP_PASSWORD !}",
    "use_tls": true,
    "use_ssl": false
  }
}
```

### API Service Configuration
```json
{
  "api_config": {
    "api_key": "{! env.SENDGRID_API_KEY !}",
    "api_url": "https://api.sendgrid.com/v3/mail/send",
    "region": "us-east-1"
  }
}
```

### Attachments
```json
{
  "attachments": [
    {
      "file_path": "path/to/document.pdf",
      "filename": "Report.pdf"
    },
    {
      "file_path": "path/to/image.png",
      "filename": "Logo.png",
      "inline": true,
      "cid": "company_logo"
    }
  ]
}
```

## Expression System

All string values support expressions for dynamic content:

### Environment Variables
```json
{
  "username": "{! env.GMAIL_USER !}",
  "password": "{! env.GMAIL_APP_PASSWORD !}"
}
```

### Date/Time
```json
{
  "subject": "Daily Report - {! datetime.now().strftime('%Y-%m-%d') !}",
  "body_text": "Generated at: {! datetime.now().isoformat() !}"
}
```

### Variables and Context
```json
{
  "vars": {
    "campaign_name": "Summer Sale",
    "discount": "20%"
  },
  "subject": "{{campaign_name}} - Save {{discount}} today!"
}
```

## Common Use Cases

### 1. Welcome Email
Send personalized welcome emails to new users.

### 2. Order Confirmations
Automated order confirmation emails with order details.

### 3. Password Reset
Secure password reset emails with temporary links.

### 4. Newsletter
Mass newsletter distribution with personalization.

### 5. Reports with Attachments
Automated reports with PDF attachments and inline charts.

### 6. Transactional Emails
System notifications, alerts, and status updates.

### 7. Marketing Campaigns
Personalized marketing emails with dynamic content.

### 8. System Monitoring
Automated alerts and monitoring notifications.

## Environment Variables

Create a `.env` file with your email service credentials:

```bash
# Gmail SMTP
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-gmail-app-password

# SendGrid API
SENDGRID_API_KEY=SG.your-sendgrid-api-key

# Custom SMTP
SMTP_HOST=your-smtp-server.com
SMTP_PORT=587
SMTP_USER=your-username
SMTP_PASSWORD=your-password

# Email addresses
FROM_EMAIL=sender@yourdomain.com
FROM_NAME=Your Service Name
```

## Testing

Run the comprehensive test suite:

```bash
cd mcp_server/tools/lng_email_client/stuff
python test_email_client.py
```

Tests include:
- Email address validation
- SMTP configuration
- API service configuration
- Template processing
- Batch email processing
- Attachment handling
- Expression system
- Session management
- Configuration file loading

## Security Notes

- Store sensitive credentials in environment variables
- Use app-specific passwords for Gmail
- Enable 2FA on email accounts
- Rotate API keys regularly
- Use TLS/SSL for SMTP connections
- Validate email addresses before sending
- Implement rate limiting for batch operations

## Error Handling

The tool includes comprehensive error handling for:
- Invalid email addresses
- SMTP connection failures
- API authentication errors
- Template rendering errors
- File attachment issues
- Network timeouts
- Rate limiting violations

## Performance

- Batch processing with configurable delays
- Connection pooling for SMTP
- Async operations for API services
- Memory-efficient attachment handling
- Session persistence across calls
- Retry logic with exponential backoff
