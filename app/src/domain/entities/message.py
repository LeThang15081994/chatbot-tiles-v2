"""
Message Entity
Represents a single message in a conversation
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from .tool_call import ToolCall


class MessageRole(str, Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Message:
    """
    Message entity

    Represents a single message in the conversation.
    Can be from user, assistant, system, or tool.
    """

    content: str
    role: MessageRole
    message_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    tool_calls: List['ToolCall'] = field(default_factory=list)

    def add_tool_call(self, tool_call: 'ToolCall') -> None:
        """
        Add a tool call to this message

        Args:
            tool_call: Tool call to add
        """
        self.tool_calls.append(tool_call)

    def has_tool_calls(self) -> bool:
        """Check if message has tool calls"""
        return len(self.tool_calls) > 0

    def is_user_message(self) -> bool:
        """Check if this is a user message"""
        return self.role == MessageRole.USER

    def is_assistant_message(self) -> bool:
        """Check if this is an assistant message"""
        return self.role == MessageRole.ASSISTANT

    def is_system_message(self) -> bool:
        """Check if this is a system message"""
        return self.role == MessageRole.SYSTEM

    def is_tool_message(self) -> bool:
        """Check if this is a tool message"""
        return self.role == MessageRole.TOOL

    def truncate_content(self, max_length: int = 500) -> str:
        """
        Get truncated content

        Args:
            max_length: Maximum content length

        Returns:
            Truncated content
        """
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."

    def to_dict(self) -> dict:
        """Convert to dictionary format"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        """
        Create message from dictionary

        Args:
            data: Dictionary with message data

        Returns:
            Message instance
        """
        return cls(
            content=data["content"],
            role=MessageRole(data["role"]),
            metadata=data.get("metadata", {})
        )

    def __repr__(self) -> str:
        content_preview = self.truncate_content(50)
        return f"Message(role={self.role.value}, content='{content_preview}')"

