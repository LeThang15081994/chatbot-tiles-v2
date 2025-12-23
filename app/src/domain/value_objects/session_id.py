"""
Session ID Value Object
"""
from dataclasses import dataclass
from uuid import UUID, uuid4
from typing import Optional


@dataclass(frozen=True)
class SessionId:
    """
    Session ID value object

    Immutable identifier for chat sessions.
    Ensures valid session IDs throughout the system.
    """

    value: str

    def __post_init__(self):
        """Validate session ID format"""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Session ID must be a non-empty string")

        if len(self.value) > 255:
            raise ValueError("Session ID too long (max 255 characters)")

    @classmethod
    def generate(cls) -> 'SessionId':
        """
        Generate a new random session ID

        Returns:
            New SessionId instance
        """
        return cls(value=str(uuid4()))

    @classmethod
    def from_string(cls, session_id: str) -> 'SessionId':
        """
        Create SessionId from string

        Args:
            session_id: Session ID string

        Returns:
            SessionId instance
        """
        return cls(value=session_id)

    def is_valid_uuid(self) -> bool:
        """
        Check if session ID is a valid UUID

        Returns:
            True if valid UUID format
        """
        try:
            UUID(self.value)
            return True
        except (ValueError, AttributeError):
            return False

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"SessionId('{self.value}')"

