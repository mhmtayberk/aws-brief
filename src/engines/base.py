from abc import ABC, abstractmethod

class BaseEngine(ABC):
    """
    Abstract Base Class for AI Engines.
    Enforces the implementation of the `summarize` method.
    """
    @abstractmethod
    def summarize(self, text: str) -> str:
        """
        Summarize the provided text.
        
        Args:
            text (str): The text to summarize.
            
        Returns:
            str: The summary.
        """
        pass
