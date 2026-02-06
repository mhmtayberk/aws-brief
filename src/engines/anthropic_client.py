import logging
from .base import BaseEngine
from src.utils.config import settings

logger = logging.getLogger(__name__)

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

class AnthropicEngine(BaseEngine):
    """
    AI Engine for Anthropic (Claude) API.
    """
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        if not Anthropic:
             raise ImportError("anthropic library not installed. Install with `pip install anthropic`")
             
        api_key = settings.ANTHROPIC_API_KEY.get_secret_value() if settings.ANTHROPIC_API_KEY else None
        if not api_key:
             logger.warning("Anthropic API Key not found.")
        
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def summarize(self, text: str) -> str:
        try:
            logger.info(f"Summarizing text with Anthropic model: {self.model}")
            
            # Use centralized prompts
            from src.utils.prompts import get_system_prompt, get_summarize_prompt
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0,
                system=get_system_prompt(),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": get_summarize_prompt(text)
                            }
                        ]
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic summarization failed: {e}")
            raise
