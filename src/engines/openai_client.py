import logging
from .base import BaseEngine
from src.utils.config import settings

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class OpenAIEngine(BaseEngine):
    """
    AI Engine for OpenAI API.
    """
    def __init__(self, model: str = "gpt-4o-mini"):
        if not OpenAI:
             raise ImportError("openai library not installed.")
             
        api_key = settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else None
        if not api_key:
             logger.warning("OpenAI API Key not found.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def summarize(self, text: str) -> str:
        try:
            logger.info(f"Summarizing text with OpenAI model: {self.model}")
            
            # Use centralized prompts
            from src.utils.prompts import get_system_prompt, get_summarize_prompt
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": get_summarize_prompt(text)}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI summarization failed: {e}")
            raise
