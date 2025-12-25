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
            
            prompt = f"""
            Role: Senior Cloud Architect
            Output Language: {settings.SUMMARY_LANGUAGE}
            
            Analyze this AWS update:
            1. Title (Punchy)
            2. The What (Technical)
            3. The Why (Impact)
            4. Impact Level [CRITICAL/HIGH/MEDIUM/LOW]
            5. Action Required (Yes/No)

            Text:
            {text}
            """
            
            response = self.client.models.generate_content(
                model=self.model_name, 
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini summarization failed: {e}")
            raise
