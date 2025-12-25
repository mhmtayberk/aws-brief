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
    def __init__(self, model: str = "gpt-3.5-turbo"):
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": f"You are a Senior Cloud Architect & Security Analyst. Output Language: {settings.SUMMARY_LANGUAGE}. Format: Markdown."
                    },
                    {
                        "role": "user", 
                        "content": f"""
                        Analyze this AWS update:
                        
                        Instructions:
                        1. Title: Punchy 5-8 words.
                        2. The "What": Technical explanation.
                        3. The "Why": Value/Impact.
                        4. Impact Level: [CRITICAL/HIGH/MEDIUM/LOW/INFO].
                        5. Action Required: Yes for upgrade/patch, No otherwise.

                        Text:
                        {text}
                        """
                    }
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI summarization failed: {e}")
            raise
