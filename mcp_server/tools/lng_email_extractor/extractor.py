"""
Extraction module for parsing and decoding emails.
"""
import email
from email.header import decode_header
import datetime

def decode_mime_words(s):
    decoded = decode_header(s)
    return ''.join([
        part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part
        for part, encoding in decoded
    ])

def extract_email_fields(msg, mailbox):
    subject = decode_mime_words(msg.get('Subject', ''))
    sender = decode_mime_words(msg.get('From', ''))
    date = msg.get('Date', '')
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True)
                if body:
                    body = body.decode(part.get_content_charset() or 'utf-8', errors='replace')
                break
    else:
        body = msg.get_payload(decode=True)
        if body:
            body = body.decode(msg.get_content_charset() or 'utf-8', errors='replace')
    return {
        'id': None,  # to be set by caller
        'subject': subject,
        'from': sender,
        'date': date,
        'body': body,
        'mailbox': mailbox,
        'extracted_at': datetime.datetime.now().isoformat()
    }
