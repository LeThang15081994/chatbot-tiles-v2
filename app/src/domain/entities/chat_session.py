"""
Chat Session Entity
Represents a conversation session in the RAG system
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from .message import Message


@dataclass
class ChatSession:
    """
    Chat session entity - Aggregate root

    Represents a complete conversation session with history and context.
    This is the core entity in the RAG domain.
    """

    session_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None
    messages: List['Message'] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def add_message(self, message: 'Message') -> None:
        """
        Add a message to the session

        Args:
            message: Message to add
        """
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_recent_messages(self, count: int = 10) -> List['Message']:
        """
        Get recent messages from the session

        Args:
            count: Number of recent messages to return

        Returns:
            List of recent messages
        """
        return self.messages[-count:] if self.messages else []

    def get_messages_for_context(self, max_messages: int = 12) -> List['Message']:
        """
        Get messages suitable for LLM context

        Args:
            max_messages: Maximum number of messages

        Returns:
            List of messages for context
        """
        return self.messages[-max_messages:]

    def message_count(self) -> int:
        """Get total message count"""
        return len(self.messages)

    def get_conversation_summary(self) -> str:
        """
        Get a text summary of the conversation

        Returns:
            Formatted conversation text
        """
        if not self.messages:
            return ""

        lines = []
        for msg in self.messages:
            role = msg.role.value.capitalize()
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def clear_old_messages(self, keep_count: int = 10) -> int:
        """
        Clear old messages, keeping only recent ones

        Args:
            keep_count: Number of messages to keep

        Returns:
            Number of messages removed
        """
        if len(self.messages) <= keep_count:
            return 0

        removed_count = len(self.messages) - keep_count
        self.messages = self.messages[-keep_count:]
        self.updated_at = datetime.now()

        return removed_count

    def update_metadata(self, key: str, value: any) -> None:
        """Update session metadata"""
        self.metadata[key] = value
        self.updated_at = datetime.now()

    def __repr__(self) -> str:
        return f"ChatSession(id={self.session_id}, messages={len(self.messages)}, user={self.user_id})"

