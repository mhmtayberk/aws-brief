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

try:
    from .mistral_client import MistralEngine
except ImportError:
    MistralEngine = None

try:
    from .deepseek_client import DeepSeekEngine
except ImportError:
    DeepSeekEngine = None

EngineType = Literal["ollama", "openai", "anthropic", "transformers", "gemini", "groq", "mistral", "deepseek"]

class EngineFactory:
    """
    Factory to instantiate the correct AI Engine based on configuration.
    """
    @staticmethod
    def get_engine(engine_type: str, model: str = None) -> BaseEngine:
        engine_type = engine_type.lower()
        
        if engine_type == "ollama":
            return OllamaEngine(model=model or "llama3.3")
        elif engine_type == "openai":
            return OpenAIEngine(model=model or "gpt-4o-mini")
        elif engine_type == "anthropic":
            if not AnthropicEngine:
                 raise ImportError("Anthropic dependency missing.")
            return AnthropicEngine(model=model or "claude-3-5-sonnet-20241022")
        elif engine_type == "transformers":
             if not TransformersEngine:
                 raise ImportError("Transformers/Torch dependency missing.")
             return TransformersEngine(model=model or "facebook/bart-large-cnn")
        elif engine_type == "gemini":
             if not GeminiEngine:
                 raise ImportError("Google Generative AI dependency missing.")
             return GeminiEngine(model=model or "gemini-2.0-flash")
        elif engine_type == "groq":
             if not GroqEngine:
                 raise ImportError("Groq dependency missing.")
             return GroqEngine(model=model or "mixtral-8x7b-32768")
        elif engine_type == "mistral":
             if not MistralEngine:
                 raise ImportError("Mistral dependency missing. Install with: pip install mistralai")
             return MistralEngine(model=model or "mistral-large-latest")
        elif engine_type == "deepseek":
             if not DeepSeekEngine:
                 raise ImportError("DeepSeek requires OpenAI library. Install with: pip install openai")
             return DeepSeekEngine(model=model or "deepseek-chat")
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")

    @staticmethod
    def get_engine_with_fallback(
        engine_type: str, 
        model: str = None,
        fallback_chain: list = None
    ) -> BaseEngine:
        """
        Get engine with fallback chain.
        If primary engine fails, try fallback engines in order.
        
        Args:
            engine_type: Primary engine to try
            model: Model to use (optional)
            fallback_chain: List of fallback engines (default: ["openai", "anthropic", "ollama"])
        
        Returns:
            BaseEngine instance
        
        Raises:
            Exception: If all engines fail
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Default fallback chain
        if fallback_chain is None:
            fallback_chain = ["openai", "anthropic", "ollama"]
        
        # Build engines to try: primary + fallbacks (excluding primary if already in fallbacks)
        engines_to_try = [engine_type] + [e for e in fallback_chain if e != engine_type]
        
        last_error = None
        for engine in engines_to_try:
            try:
                logger.info(f"Attempting to initialize engine: {engine}")
                return EngineFactory.get_engine(engine, model)
            except Exception as e:
                logger.warning(f"Engine {engine} initialization failed: {e}")
                last_error = e
                continue
        
        # All engines failed
        error_msg = f"All engines failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
