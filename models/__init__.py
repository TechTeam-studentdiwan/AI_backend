from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from .hospital import Hospital
from .patient import Patient


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class Conversation(BaseModel):
    conversation_id: str
    user_id: Optional[str] = None
    title: Optional[str] = None
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True

# Request/Response Models
class StartConversationRequest(BaseModel):
    user_id: Optional[str] = None
    initial_message: Optional[str] = None
    system_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class StartConversationResponse(BaseModel):
    conversation_id: str
    created_at: datetime

class AddMessageRequest(BaseModel):
    message: str
    metadata: Optional[Dict[str, Any]] = None

class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None


__all__ = ["Hospital", "Patient"]