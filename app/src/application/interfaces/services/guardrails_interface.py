"""
Guardrails Service Interface
Domain interface for input/output validation
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class IGuardrailsService(ABC):
    """Domain interface for Guardrails service"""

    @abstractmethod
    async def validate_input(
        self,
        messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Validate input messages

        Args:
            messages: Input messages to validate

        Returns:
            Validation result with:
            - blocked: bool
            - messages: List[Dict]
            - altered: bool
            - altered_user_message: Optional[str]
        """
        pass

