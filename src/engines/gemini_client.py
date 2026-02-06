import logging
from .base import BaseEngine
from src.utils.config import settings

logger = logging.getLogger(__name__)

try:
    from google import genai
except ImportError:
    genai = None

class GeminiEngine(BaseEngine):
    """
    AI Engine for Google Gemini (Vertex AI / Studio) using new google-genai SDK.
    """
    def __init__(self, model: str = "gemini-2.0-flash"):
        if not genai:
             raise ImportError("google-genai library not installed.")
             
        api_key = settings.GOOGLE_API_KEY.get_secret_value() if settings.GOOGLE_API_KEY else None
        if not api_key:
             logger.warning("Google API Key not found.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model

    def summarize(self, text: str) -> str:
        try:
            logger.info(f"Summarizing text with Google Gemini model: {self.model_name}")
            
            # Use centralized prompts
            from src.utils.prompts import get_system_prompt, get_summarize_prompt
            
            # Combine system and user prompts for Gemini
            full_prompt = f"{get_system_prompt()}\n\n{get_summarize_prompt(text)}"
            
            response = self.client.models.generate_content(
                model=self.model_name, 
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini summarization failed: {e}")
            raise
