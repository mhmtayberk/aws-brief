import logging
from .base import BaseEngine
from src.utils.config import settings

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class DeepSeekEngine(BaseEngine):
    """
    AI Engine for DeepSeek API (OpenAI-compatible).
    
    DeepSeek provides cost-effective AI models with OpenAI-compatible API.
    Extremely affordable pricing ($0.14/1M tokens) with GPT-4 level performance.
    """
    def __init__(self, model: str = "deepseek-chat"):
        if not OpenAI:
            raise ImportError("openai library not installed. DeepSeek uses OpenAI-compatible API.")
        
        api_key = settings.DEEPSEEK_API_KEY.get_secret_value() if settings.DEEPSEEK_API_KEY else None
        if not api_key:
            logger.warning("DeepSeek API Key not found.")
        
        # DeepSeek uses OpenAI-compatible API with custom base URL
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = model
    
    def summarize(self, text: str) -> str:
        try:
            logger.info(f"Summarizing text with DeepSeek model: {self.model}")
            
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
            logger.error(f"DeepSeek summarization failed: {e}")
            raise
