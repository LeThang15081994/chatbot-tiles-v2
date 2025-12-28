"""
Guardrails Service Implementation
Handles input/output validation with NeMo Guardrails
"""
import os
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
from nemoguardrails import LLMRails, RailsConfig

from app.src.application.interfaces.services.guardrails_interface import IGuardrailsService
from app.src.infrastructure.config.settings import GuardrailsSettings

logger = logging.getLogger(__name__)

# Module-level cache for RailsConfig (loaded once at startup, reused for all instances)
_cached_config: Optional[RailsConfig] = None
_config_path: Optional[str] = None


class GuardrailsService(IGuardrailsService):
    """
    NeMo Guardrails service

    Provides:
    - Input validation (blocking harmful content)
    - Output validation (filtering unsafe responses)
    - PII masking
    - Streaming support
    """

    def __init__(self, settings: GuardrailsSettings):
        """
        Initialize Guardrails service

        Args:
            settings: Guardrails configuration settings
        """
        self.settings = settings
        self.rails: Optional[LLMRails] = None
        self._initialize()

    def _load_guardrails_config(self) -> Optional[RailsConfig]:
        """
        Load guardrails config once and cache it for reuse

        This method loads the config from file and caches it at module level.
        Subsequent calls return the cached config.

        Returns:
            RailsConfig instance if loaded successfully, None otherwise
        """
        global _cached_config, _config_path

        # Return cached config if already loaded
        if _cached_config is not None:
            logger.debug(f"Reusing cached guardrails config from: {_config_path}")
            return _cached_config

        try:
            config_path = self.settings.CONFIG_PATH

            # Check if config path exists
            if not os.path.exists(config_path):
                logger.warning(
                    f"Guardrails config path not found: {config_path}. "
                    "Guardrails will be disabled."
                )
                return None

            # Load config from file
            logger.info(f"Loading guardrails config from: {config_path}")
            config = RailsConfig.from_path(config_path)

            # Cache config for reuse
            _cached_config = config
            _config_path = config_path

            return config

        except Exception as e:
            logger.error(
                f"Failed to load guardrails config: {e}",
                exc_info=True
            )
            raise

    def _initialize(self) -> None:
        """Initialize NeMo Guardrails using cached config"""
        try:
            # Load config (will use cached if already loaded)
            config = self._load_guardrails_config()

            if config is None:
                logger.warning(
                    "Guardrails config not available. "
                    "Guardrails will be disabled."
                )
                self.rails = None
                return

            # Initialize LLMRails with config
            self.rails = LLMRails(config)
            logger.info("Guardrails initialized successfully using cached config")

        except Exception as e:
            logger.warning(f"Failed to initialize Guardrails: {e}. Guardrails will be disabled.")
            self.rails = None

    async def validate_input(
        self,
        messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Validate input messages

        Args:
            messages: Input messages to validate

        Returns:
            Validation result with modified messages if needed
        """
        try:
            if not self.rails:
                # Guardrails not available, return safe defaults
                return {
                    "blocked": False,
                    "messages": messages,
                    "altered": False,
                    "altered_user_message": None
                }

            # Run input validation rails only
            result = await self.rails.generate_async(
                messages=messages,
                options={"rails": ["input"]}
            )

            # Extract response messages
            response_msgs = result.response if hasattr(result, "response") else []

            # Check if blocked
            blocked = self._is_blocked(response_msgs)

            # Check if messages were altered (PII masked)
            altered = self._is_altered(messages, response_msgs)

            # Get altered user message if available
            altered_user_message = None
            if altered:
                user_msg = next(
                    (m.get("content") for m in response_msgs if m.get("role") == "user"),
                    None
                )
                if user_msg:
                    altered_user_message = user_msg

            return {
                "blocked": blocked,
                "messages": response_msgs,
                "altered": altered,
                "altered_user_message": altered_user_message
            }

        except Exception as e:
            raise RuntimeError(f"Input validation failed: {e}")

    async def stream_with_validation(
        self,
        messages: List[Dict[str, str]],
        generator: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """
        Stream output with validation

        Args:
            messages: Context messages
            generator: Token generator from LLM

        Yields:
            Validated tokens
        """
        try:
            if not self.rails:
                # Guardrails not available, pass through without validation
                async for chunk in generator:
                    yield chunk
                return

            # Stream through guardrails
            async for chunk in self.rails.stream_async(
                messages=messages,
                generator=generator
            ):
                if not self._is_guardrails_error(chunk):
                    yield chunk
                else:
                    # Block detected
                    raise ValueError("Output blocked by guardrails")

        except Exception as e:
            raise RuntimeError(f"Streaming validation failed: {e}")

    def _is_blocked(self, response: List[Dict[str, str]]) -> bool:
        """Check if response was blocked"""
        if not response:
            return False

        # Check for assistant message with blocking content
        for msg in response:
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                content_lower = content.lower()

                # Common blocking messages (case-insensitive)
                blocking_indicators = [
                    "i'm sorry, i can't respond to that",
                    "i'm sorry, i can't",
                    "i cannot respond",
                    "content blocked",
                    "blocked by guardrails"
                ]

                if any(indicator in content_lower for indicator in blocking_indicators):
                    return True

        return False

    def _is_altered(
        self,
        original: List[Dict[str, str]],
        modified: List[Dict[str, str]]
    ) -> bool:
        """Check if messages were altered (PII masked)"""
        if len(original) != len(modified):
            return True

        # Check user messages for alterations (PII masking)
        for orig, mod in zip(original, modified):
            if orig.get("role") == "user" and mod.get("role") == "user":
                if orig.get("content") != mod.get("content"):
                    return True

        return False

    def _is_guardrails_error(self, chunk: str) -> bool:
        """Check if chunk is a guardrails error"""
        if not chunk:
            return False

        # Convert to string and lowercase for case-insensitive matching
        chunk_str = str(chunk).lower()

        # Error indicators (matching code cũ)
        error_indicators = [
            "guardrails_violation",
            "blocked by self check output rails",
            "content_blocked",
            "i'm sorry, i can't respond to that",
            '"error":',
            "blocked by guardrails",
            "i'm sorry, i can't",
            "[blocked by guardrails]",
            "content filtered"
        ]

        return any(indicator.lower() in chunk_str for indicator in error_indicators)

    async def reset(self) -> None:
        """Reset guardrails runtime state"""
        try:
            if self.rails and hasattr(self.rails, "runtime"):
                if hasattr(self.rails.runtime, "reset"):
                    await self.rails.runtime.reset()
        except Exception:
            pass

    def health_check(self) -> bool:
        """Check Guardrails health"""
        try:
            return self.rails is not None
        except Exception:
            return False

