from pydantic import BaseModel


class LLMPrompt(BaseModel):
    """A prompt for a language model"""

    system: str
    user: str
    version: str
    model: str = "claude-4-5-sonnet"
