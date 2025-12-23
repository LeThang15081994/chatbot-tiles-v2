"""
Prompt Template Value Object
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class PromptTemplate:
    """
    Prompt template value object

    Represents a prompt template for LLM.
    Immutable to ensure template integrity.
    """

    template: str
    name: str = "default"
    variables: tuple = ()  # Tuple of variable names
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate prompt template"""
        if not self.template:
            raise ValueError("Template cannot be empty")

        # Convert list to tuple if needed
        if isinstance(self.variables, list):
            object.__setattr__(self, 'variables', tuple(self.variables))

    @classmethod
    def from_string(
        cls,
        template: str,
        name: str = "default",
        variables: Optional[list] = None
    ) -> 'PromptTemplate':
        """
        Create PromptTemplate from string

        Args:
            template: Template string
            name: Template name
            variables: List of variable names

        Returns:
            PromptTemplate instance
        """
        return cls(
            template=template,
            name=name,
            variables=tuple(variables) if variables else ()
        )

    def format(self, **kwargs) -> str:
        """
        Format template with variables

        Args:
            **kwargs: Variable values

        Returns:
            Formatted prompt string
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing variable in template: {e}")

    def validate_variables(self, **kwargs) -> bool:
        """
        Check if all required variables are provided

        Args:
            **kwargs: Variable values

        Returns:
            True if all variables present
        """
        return all(var in kwargs for var in self.variables)

    def get_placeholder_count(self) -> int:
        """
        Count placeholders in template

        Returns:
            Number of placeholders
        """
        import re
        return len(re.findall(r'\{([^}]+)\}', self.template))

    def __repr__(self) -> str:
        template_preview = self.template[:50] + "..." if len(self.template) > 50 else self.template
        return f"PromptTemplate(name='{self.name}', template='{template_preview}')"

