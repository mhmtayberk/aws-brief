import logging
try:
    import ollama
except ImportError:
    ollama = None

from .base import BaseEngine
from src.utils.config import settings

logger = logging.getLogger(__name__)

class OllamaEngine(BaseEngine):
    """
    AI Engine for local Ollama instance.
    """
    def __init__(self, model: str = "llama3.3"):
        self.model = model
        host = settings.OLLAMA_HOST
        # Ensure proper initialization of client if library supports it, 
        # otherwise basic usage might differ. Assuming standard python-ollama lib.
        if ollama:
            self.client = ollama.Client(host=host)
        else:
            logger.warning("Ollama library not installed. Functionality will be limited.")
            self.client = None

    def summarize(self, text: str) -> str:
        if not self.client:
            raise RuntimeError("Ollama library not installed.")
        
        try:
            logger.info(f"Summarizing text with Ollama model: {self.model}")
            
            # Use centralized prompts
            from src.utils.prompts import get_system_prompt, get_summarize_prompt
            
            # Combine system and user prompts for Ollama
            full_prompt = f"{get_system_prompt()}\n\n{get_summarize_prompt(text)}"
            
            response = self.client.generate(model=self.model, prompt=full_prompt)
            return response.get('response', '')
        except Exception as e:
            logger.error(f"Ollama summarization failed: {e}")
            raise
