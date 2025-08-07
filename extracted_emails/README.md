# Extracted Emails Directory

This directory contains JSON files with extracted unread emails from various mailboxes.

## File Management

- **Automatic Creation**: Email JSON files are automatically created when using the email extractor tool
- **Naming Convention**: `emails_{mailbox}_{timestamp}.json` or custom filename if specified
- **Weekly Cleanup**: Files should be reviewed and deleted weekly as agreed with the user
- **File Format**: JSON format with email metadata and content

## File Structure

Each JSON file contains:
```json
{
  "success": true,
  "message": "Status message",
  "mailbox": "gmail|mailru_1|mailru_2",
  "period_days": 7,
  "total_emails": 5,
  "emails": [
    {
      "id": "email_id",
      "subject": "Email subject",
      "from": "sender@example.com",
      "to": "recipient@example.com",
      "date": "Email date",
      "body": "Email content",
      "mailbox": "source_mailbox",
      "extracted_at": "2025-08-07T10:30:00"
    }
  ]
}
```

## Security Notes

- Files may contain sensitive email content
- Review files before sharing or archiving
- Delete files regularly to maintain privacy
- Ensure proper file permissions are set
