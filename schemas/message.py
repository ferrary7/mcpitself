from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
from datetime import datetime

class MessageType(str, Enum):
    TASK = "task"
    RESPONSE = "response"
    QUERY = "query"
    NOTIFICATION = "notification"
    ERROR = "error"

class MessagePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Message(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    sender: str
    recipient: str
    message_type: MessageType
    priority: MessagePriority = MessagePriority.MEDIUM
    content: Dict[str, Any]
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    assigned_to: str
    created_by: str
    status: str = "pending"
    priority: MessagePriority = MessagePriority.MEDIUM
    dependencies: List[str] = Field(default_factory=list)
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Dict[str, Any]
    message: str
    completed_at: datetime = Field(default_factory=datetime.now)