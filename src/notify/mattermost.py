import logging
import requests
from .base import BaseNotifier
from src.utils.config import settings

logger = logging.getLogger(__name__)

class MattermostNotifier(BaseNotifier):
    """
    Notifier for Mattermost via Incoming Webhooks.
    
    Mattermost is an open-source, self-hosted team collaboration platform.
    This notifier sends formatted messages to Mattermost channels via webhooks.
    """
    def __init__(self):
        self.webhook_url = settings.MATTERMOST_WEBHOOK_URL
    
    def send(self, title: str, message: str, url: str, category: str = "General") -> bool:
        if not self.webhook_url:
            logger.error("Cannot send Mattermost notification: Webhook URL missing.")
            return False
        
        # Emoji mapping for visual categorization
        emoji = "📢"
        cat_lower = category.lower()
        if "security" in cat_lower: 
            emoji = "🛡️"
        elif "database" in cat_lower: 
            emoji = "🗄️"
        elif "compute" in cat_lower or "serverless" in cat_lower: 
            emoji = "⚡"
        elif "container" in cat_lower: 
            emoji = "📦"
        elif "ai" in cat_lower or "machine learning" in cat_lower: 
            emoji = "🤖"
        elif "cost" in cat_lower: 
            emoji = "💰"
        elif "architecture" in cat_lower: 
            emoji = "🏗️"
        elif "critical" in cat_lower:
            emoji = "🚨"
        
        # Mattermost webhook payload
        # Supports Markdown formatting
        formatted_message = f"{emoji} **{category}**: {title}\n\n{message}\n\n[Read More]({url})"
        
        payload = {
            "text": formatted_message,
            "username": "AWS Brief Bot"
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Mattermost notification sent for: {title}")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to send Mattermost notification: {e}")
            return False
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid Mattermost payload: {e}")
            return False
