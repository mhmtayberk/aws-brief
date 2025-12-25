from abc import ABC, abstractmethod

class BaseNotifier(ABC):
    """
    Abstract Base Class for Notification Providers.
    """
    @abstractmethod
    def send(self, title: str, message: str, url: str, category: str = "General") -> bool:
        """
        Send a notification.

        Args:
            title (str): Title of the news item.
            message (str): Summary or body of the notification.
            url (str): Link to the original source.
            category (str): Category or feed name.

        Returns:
            bool: True if sent successfully, False otherwise.
        """
        pass
