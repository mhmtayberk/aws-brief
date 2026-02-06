import logging
from .base import BaseEngine
from src.utils.config import settings

logger = logging.getLogger(__name__)

try:
    from groq import Groq
except ImportError:
    Groq = None

class GroqEngine(BaseEngine):
    """
    AI Engine for Groq (LPU Inference).
    """
    def __init__(self, model: str = "mixtral-8x7b-32768"):
        if not Groq:
             raise ImportError("groq library not installed.")
             
        api_key = settings.GROQ_API_KEY.get_secret_value() if settings.GROQ_API_KEY else None
        if not api_key:
             logger.warning("Groq API Key not found.")
        
        self.client = Groq(api_key=api_key)
        self.model = model

    def summarize(self, text: str) -> str:
        try:
            logger.info(f"Summarizing text with Groq model: {self.model}")
            
            # Use centralized prompts
            from src.utils.prompts import get_system_prompt, get_summarize_prompt
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": get_summarize_prompt(text)}
                ],
                model=self.model,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq summarization failed: {e}")
            raise
