import os
from typing import List
import anyio
import functools
from pydantic_ai import Tool
import logging
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from datetime import datetime
from models.email import EmailSendInput, EmailMessage
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class EmailTool:
    """Tool for email operations."""
    
    def __init__(self):
        """Initialize with credentials from environment variables."""
        # Try loading .env file if vars aren't set
        load_dotenv()
        
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.imap_server = os.getenv('IMAP_SERVER')
        self.imap_port = int(os.getenv('IMAP_PORT', '993'))
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.password = os.getenv('EMAIL_PASSWORD')
        
        if not all([self.smtp_server, self.imap_server, self.email_address, self.password]):
            raise ValueError(
                "Missing required email configuration. Please ensure these environment variables are set:\n"
                "- SMTP_SERVER\n"
                "- IMAP_SERVER\n"
                "- EMAIL_ADDRESS\n"
                "- EMAIL_PASSWORD\n"
                "And optionally:\n"
                "- SMTP_PORT (default: 587)\n"
                "- IMAP_PORT (default: 993)"
            )

    async def send_email(self, input: EmailSendInput) -> bool:
        """Send an email to the specified recipient."""
        try:
            send_fn = functools.partial(
                self._send_email,
                recipient=input.recipient,
                subject=input.subject,
                body=input.body
            )
            return await anyio.to_thread.run_sync(send_fn)
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise RuntimeError(f"Failed to send email: {e}")

    async def read_inbox_emails(self, unread_only: bool = False, limit: int = 10) -> List[EmailMessage]:
        """Read emails specifically from the inbox folder."""
        try:
            read_fn = functools.partial(
                self._read_emails,
                folder='inbox',
                unread_only=unread_only,
                limit=limit
            )
            return await anyio.to_thread.run_sync(read_fn)
        except Exception as e:
            logger.error(f"Failed to read inbox emails: {e}")
            return []

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read."""
        try:
            mark_fn = functools.partial(self._mark_as_read, message_id)
            return await anyio.to_thread.run_sync(mark_fn)
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")
            raise RuntimeError(f"Failed to mark email as read: {e}")

    # Internal sync implementations
    def _send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Sync implementation of send_email."""
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.email_address
        msg['To'] = recipient

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.email_address, self.password)
            server.send_message(msg)
        return True

    def _read_emails(self, folder: str, unread_only: bool, limit: int) -> List[EmailMessage]:
        """Sync implementation of read_emails with folder support."""
        emails = []
        with imaplib.IMAP4_SSL(self.imap_server, self.imap_port) as mail:
            mail.login(self.email_address, self.password)
            mail.select(folder)

            status, messages = mail.search(None, 'UNSEEN' if unread_only else 'ALL')
            if status != 'OK':
                return []
                
            for msg_id in messages[0].split()[:limit]:
                status, msg_data = mail.fetch(msg_id, '(BODY.PEEK[])')
                if status != 'OK':
                    continue
                    
                msg = email.message_from_bytes(msg_data[0][1])
                emails.append({
                    "sender": msg['from'],
                    "recipient": msg['to'],
                    "subject": msg['subject'],
                    "body": self._extract_email_body(msg),
                    "date": self._parse_email_date(msg['date']),
                    "read": False,
                    "message_id": msg_id.decode()
                })
        
        # Sort by date (newest first)
        return sorted(emails, key=lambda x: x['date'], reverse=True)

    def _mark_as_read(self, message_id: str) -> bool:
        """Sync implementation of mark_as_read."""
        with imaplib.IMAP4_SSL(self.imap_server, self.imap_port) as mail:
            mail.login(self.email_address, self.password)
            mail.select('inbox')
            mail.store(message_id, '+FLAGS', '\\Seen')
        return True

    def _extract_email_body(self, msg: email.message.Message) -> str:
        """Extract the body content from an email message."""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    return part.get_payload(decode=True).decode()
        return msg.get_payload(decode=True).decode()

    def _parse_email_date(self, date_str: str) -> datetime:
        """Parse the date string from an email message."""
        try:
            email_date = datetime.strptime(
                date_str.split('(')[0].strip(), 
                '%a, %d %b %Y %H:%M:%S %z'
            )
        except (ValueError, AttributeError):
            try:
                email_date = datetime.strptime(
                    date_str.split('(')[0].strip(),
                    '%a, %d %b %Y %H:%M:%S'
                )
            except (ValueError, AttributeError):
                email_date = datetime.now()
        return email_date

# Tool registration
email_tool = EmailTool()

tools = [
    Tool(
        email_tool.read_inbox_emails,
        name="email_read_inbox",
        description="Read emails from the inbox folder"
    ),
    Tool(
        email_tool.mark_as_read,
        name="email_mark_read",
        description="Mark an email as read"
    )
]