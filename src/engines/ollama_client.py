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
    def __init__(self, model: str = "llama2"):
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
            # Depending on ollama lib version, might need different call. 
            # Using generate as per standard.
            prompt = f"""
            Role: Senior Cloud Architect & Security Analyst
            Task: Analyze the following AWS announcement.
            Target Audience: DevOps Engineers, CTOs, Cloud Architects.
            Output Language: {settings.SUMMARY_LANGUAGE}

            Instructions:
            1. Title: Create a punchy, 5-8 word title capturing the core value.
            2. The "What": 2 sentences explaining the update technically.
            3. The "Why": Why does this matter? (Cost saving? Security fix? Performance?)
            4. Impact Level: Assign one [CRITICAL, HIGH, MEDIUM, LOW, INFO] based on operational impact.
            5. Action Required: Yes/No. If Yes, briefly state what needs to be done.

            Format: Use Markdown/Bold for readability. Avoid fluff. Be direct.

            Text to Analyze:
            {text}
            """
            response = self.client.generate(model=self.model, prompt=prompt)
            return response.get('response', '')
        except Exception as e:
            logger.error(f"Ollama summarization failed: {e}")
            raise
