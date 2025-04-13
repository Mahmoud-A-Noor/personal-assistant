
from pydantic import BaseModel, Field
from typing import Optional, TypedDict
from datetime import datetime

class EmailMessage(TypedDict):
    """An email message."""
    sender: str
    """Sender's email address"""
    recipient: str
    """Recipient's email address"""
    subject: str
    """Email subject"""
    body: str
    """Email body content"""
    date: datetime
    """Email date"""
    read: bool
    """Whether email has been read"""
    message_id: Optional[str]
    """Unique message ID from server"""

class EmailSendInput(BaseModel):
    """Input for sending an email."""
    recipient: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")