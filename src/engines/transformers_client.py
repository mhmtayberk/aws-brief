import logging
import torch
from .base import BaseEngine

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline
except ImportError:
    pipeline = None

class TransformersEngine(BaseEngine):
    """
    AI Engine for Local HuggingFace Transformers.
    Ideal for offline summarization without Ollama dependency, but heavy on RAM.
    """
    def __init__(self, model: str = "facebook/bart-large-cnn"):
        if not pipeline:
             raise ImportError("transformers/torch libraries not installed. Install with `pip install transformers torch`")
        
        logger.info(f"Loading local transformer model: {model}. This may take a while...")
        try:
            # Check for MPS (Apple Silicon) or CUDA
            device = 0 if torch.cuda.is_available() else (-1)
            if torch.backends.mps.is_available():
                # device = "mps" # Transformers pipeline support for MPS varies, defaulting to CPU for stability in this demo
                pass
            
            self.summarizer = pipeline("summarization", model=model, device=device)
            self.model = model
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load transformer model: {e}")
            raise

    def summarize(self, text: str) -> str:
        try:
            logger.info(f"Summarizing text with Local Transformer model: {self.model}")
            # Truncate to avoid max length errors if text is huge
            input_text = text[:1024] 
            
            summary_list = self.summarizer(input_text, max_length=130, min_length=30, do_sample=False)
            if summary_list and len(summary_list) > 0:
                return summary_list[0]['summary_text']
            return "Summary generation failed."
        except Exception as e:
            logger.error(f"Transformer summarization failed: {e}")
            raise
