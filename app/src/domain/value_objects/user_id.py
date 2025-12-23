"""
User ID Value Object
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UserId:
    """
    User ID value object

    Immutable identifier for users.
    Ensures valid user IDs throughout the system.
    """

    value: str

    def __post_init__(self):
        """Validate user ID format"""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("User ID must be a non-empty string")

        if len(self.value) > 255:
            raise ValueError("User ID too long (max 255 characters)")

    @classmethod
    def from_string(cls, user_id: str) -> 'UserId':
        """
        Create UserId from string

        Args:
            user_id: User ID string

        Returns:
            UserId instance
        """
        return cls(value=user_id)

    @classmethod
    def anonymous(cls) -> 'UserId':
        """
        Create anonymous user ID

        Returns:
            UserId for anonymous user
        """
        return cls(value="anonymous")

    def is_anonymous(self) -> bool:
        """
        Check if this is an anonymous user

        Returns:
            True if anonymous
        """
        return self.value == "anonymous"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"UserId('{self.value}')"

