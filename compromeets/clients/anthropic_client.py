import logging
import os
from types import TracebackType
from typing import Any

from anthropic import Anthropic
from anthropic.types import TextBlock

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Client for interacting with the Anthropic Claude API"""

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in ANTHROPIC_API_KEY environment variable")
        self.model = model
        self.client = Anthropic(api_key=self.api_key)

    def complete(self, system: str, user: str, max_tokens: int = 2048, use_caching: bool = True) -> str:
        """
        Complete a prompt with Claude, using prompt caching for the system prompt.

        Args:
            system: System prompt (will be cached if use_caching=True)
            user: User message
            max_tokens: Maximum tokens to generate
            use_caching: Whether to use prompt caching for the system prompt

        Returns:
            The generated text response

        """
        # For caching, system prompt needs to be in cache_control format
        system_param: str | list[dict[str, Any]]
        if use_caching:
            system_param = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        else:
            system_param = system

        logger.debug(f"Calling Claude API with model {self.model}, caching={use_caching}")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_param,
            messages=[{"role": "user", "content": user}],  # type: ignore
        )

        # Log cache usage if available
        if hasattr(response, "usage"):
            logger.info(f"Token usage: {response.usage}")

        # Extract text from response content
        content_block = response.content[0]
        if isinstance(content_block, TextBlock):
            return content_block.text
        else:
            # Fallback for other content types
            return str(content_block)

    def close(self) -> None:
        """Anthropic client doesn't require explicit cleanup"""

    def __enter__(self) -> "AnthropicClient":
        return self

    def __exit__(
        self, exc_type: BaseException | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self.close()
