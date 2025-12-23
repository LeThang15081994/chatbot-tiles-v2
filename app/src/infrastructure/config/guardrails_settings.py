"""
Guardrails Configuration Settings
"""
from pydantic_settings import BaseSettings


class GuardrailsSettings(BaseSettings):
    """Guardrails configuration"""

    CONFIG_PATH: str = "./guardrails"
    ENABLE_INPUT_VALIDATION: bool = True
    ENABLE_OUTPUT_VALIDATION: bool = True
    ENABLE_PII_MASKING: bool = True

    # Llama Guard model via LiteLLM
    GUARD_MODEL: str = "groq-llama-guard"
    GUARD_BASE_URL: str = "http://localhost:4000"
    GUARD_API_KEY: str = "gach-llmops"

    class Config:
        env_file = ".env"
        case_sensitive = True

