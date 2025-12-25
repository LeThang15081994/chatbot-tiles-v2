"""
Guardrails Configuration Settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class GuardrailsSettings(BaseSettings):
    """Guardrails configuration"""

    CONFIG_PATH: str = Field(default="./guardrails", description="Guardrails configuration path")
    ENABLE_INPUT_VALIDATION: bool = Field(default=True, description="Enable input validation")
    ENABLE_OUTPUT_VALIDATION: bool = Field(default=True, description="Enable output validation")
    ENABLE_PII_MASKING: bool = Field(default=True, description="Enable PII masking")

    # Llama Guard model via LiteLLM
    GUARD_MODEL: str = Field(default="groq-llama-guard", description="Guardrails model")
    GUARD_BASE_URL: str = Field(default="http://localhost:4000", description="Guardrails base URL")
    GUARD_API_KEY: str = Field(default="gach-llmops", description="Guardrails API key")

    class Config:
        env_file = ".env"
        case_sensitive = True

