from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    content: str
    role: MessageRole
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)
    embedding: Optional[List[float]] = None

class Conversation(BaseModel):
    id: str
    title: str
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)