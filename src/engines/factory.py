from typing import Literal, Union
from .base import BaseEngine
from .ollama_client import OllamaEngine
from .openai_client import OpenAIEngine

try:
    from .anthropic_client import AnthropicEngine
except ImportError:
    AnthropicEngine = None

try:
    from .transformers_client import TransformersEngine
except ImportError:
    TransformersEngine = None

try:
    from .gemini_client import GeminiEngine
except ImportError:
    GeminiEngine = None

try:
    from .groq_client import GroqEngine
except ImportError:
    GroqEngine = None

EngineType = Literal["ollama", "openai", "anthropic", "transformers", "gemini", "groq"]

class EngineFactory:
    """
    Factory to instantiate the correct AI Engine based on configuration.
    """
    @staticmethod
    def get_engine(engine_type: str, model: str = None) -> BaseEngine:
        engine_type = engine_type.lower()
        
        if engine_type == "ollama":
            return OllamaEngine(model=model or "llama2")
        elif engine_type == "openai":
            return OpenAIEngine(model=model or "gpt-3.5-turbo")
        elif engine_type == "anthropic":
            if not AnthropicEngine:
                 raise ImportError("Anthropic dependency missing.")
            return AnthropicEngine(model=model or "claude-3-opus-20240229")
        elif engine_type == "transformers":
             if not TransformersEngine:
                 raise ImportError("Transformers/Torch dependency missing.")
             return TransformersEngine(model=model or "facebook/bart-large-cnn")
        elif engine_type == "gemini":
             if not GeminiEngine:
                 raise ImportError("Google Generative AI dependency missing.")
             return GeminiEngine(model=model or "gemini-pro")
        elif engine_type == "groq":
             if not GroqEngine:
                 raise ImportError("Groq dependency missing.")
             return GroqEngine(model=model or "mixtral-8x7b-32768")
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
