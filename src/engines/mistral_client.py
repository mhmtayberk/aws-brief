import logging
from .base import BaseEngine
from src.utils.config import settings

logger = logging.getLogger(__name__)

try:
    from mistralai import Mistral
except ImportError:
    Mistral = None

class MistralEngine(BaseEngine):
    """
    AI Engine for Mistral AI API.
    
    Mistral AI provides state-of-the-art open-source and commercial LLMs
    with strong performance on reasoning, coding, and multilingual tasks.
    """
    def __init__(self, model: str = "mistral-large-latest"):
        if not Mistral:
            raise ImportError("mistralai library not installed. Install with `pip install mistralai`")
        
        api_key = settings.MISTRAL_API_KEY.get_secret_value() if settings.MISTRAL_API_KEY else None
        if not api_key:
            logger.warning("Mistral API Key not found.")
        
        self.client = Mistral(api_key=api_key)
        self.model = model
    
    def summarize(self, text: str) -> str:
        try:
            logger.info(f"Summarizing text with Mistral model: {self.model}")
            
            # Use centralized prompts
            from src.utils.prompts import get_system_prompt, get_summarize_prompt
            
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": get_summarize_prompt(text)}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Mistral summarization failed: {e}")
            raise
