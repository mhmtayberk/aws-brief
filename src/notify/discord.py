import logging
import requests
import json
from .base import BaseNotifier
from src.utils.config import settings

logger = logging.getLogger(__name__)

class DiscordNotifier(BaseNotifier):
    """
    Notifier for Discord using Webhooks.
    """
    def __init__(self):
        self.webhook_url = settings.DISCORD_WEBHOOK_URL.get_secret_value() if settings.DISCORD_WEBHOOK_URL else None
        if not self.webhook_url:
            logger.warning("DISCORD_WEBHOOK_URL is not set. Discord notifications will fail.")

    def send(self, title: str, message: str, url: str, category: str = "General") -> bool:
        if not self.webhook_url:
            logger.error("Cannot send Discord notification: Webhook URL missing.")
            return False

        # Color mapping (Decimal)
        color = 3447003 # Blue
        if "security" in category.lower(): color = 15548997 # Red
        elif "cost" in category.lower(): color = 5763719 # Green

        payload = {
            "username": "AWS-Brief Agent",
            "embeds": [
                {
                    "title": f"[{category}] {title[:200]}",
                    "description": message[:2000],  # Discord limit
                    "url": url,
                    "color": color,
                    "footer": {
                        "text": "Powered by AWS-Brief"
                    }
                }
            ]
        }

        try:
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Discord notification sent for: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False
