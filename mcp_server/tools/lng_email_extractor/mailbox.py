"""
Mailbox logic module for IMAP connection and authentication.
"""
import imaplib
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class MailboxConnector:
    def __init__(self, provider, mailbox, password):
        self.provider = provider
        self.mailbox = mailbox
        self.password = password
        self.conn = None

    def connect(self):
        if self.provider == 'gmail':
            self.conn = imaplib.IMAP4_SSL('imap.gmail.com')
        elif self.provider == 'mailru':
            self.conn = imaplib.IMAP4_SSL('imap.mail.ru')
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        self.conn.login(self.mailbox, self.password)
        return self.conn

    def select_mailbox(self, box='INBOX'):
        if self.conn:
            self.conn.select(box)
        else:
            raise RuntimeError("Not connected")

    def fetch_email_ids(self, days_back=7, only_unread=True, max_emails=None, 
                       subject_filter=None, from_filter=None):
        """
        Fetch email IDs with filtering options.
        
        Args:
            days_back (int): Number of days to look back
            only_unread (bool): Whether to fetch only unread emails
            max_emails (int): Maximum number of emails to fetch (None for all)
            subject_filter (str): Filter emails by subject containing this string
            from_filter (str): Filter emails by sender containing this string
            
        Returns:
            List of email IDs matching the criteria
        """
        if not self.conn:
            raise RuntimeError("Not connected")
            
        # Build search criteria
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        date_str = start_date.strftime("%d-%b-%Y")
        
        search_criteria = []
        if only_unread:
            search_criteria.append('UNSEEN')
        search_criteria.append(f'SINCE "{date_str}"')
        
        # Convert to IMAP search string
        search_str = f'({" ".join(search_criteria)})'
        
        # Search emails
        status, data = self.conn.search(None, search_str)
        if status != 'OK':
            return []
            
        # Get email IDs
        email_ids = data[0].split()
        
        # Apply max limit
        if max_emails and len(email_ids) > max_emails:
            email_ids = email_ids[:max_emails]
            
        return email_ids
            
    def fetch_email_data(self, email_id):
        """Fetch email data for a specific email ID"""
        if not self.conn:
            raise RuntimeError("Not connected")
            
        status, msg_data = self.conn.fetch(email_id, '(RFC822)')
        if status != 'OK':
            return None
            
        return msg_data[0][1]
        
    def logout(self):
        if self.conn:
            self.conn.logout()
