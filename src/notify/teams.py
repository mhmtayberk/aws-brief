import logging
import requests
import json
from .base import BaseNotifier
from src.utils.config import settings

logger = logging.getLogger(__name__)

class TeamsNotifier(BaseNotifier):
    """
    Notifier for Microsoft Teams using Incoming Webhooks.
    """
    def __init__(self):
        self.webhook_url = settings.TEAMS_WEBHOOK_URL.get_secret_value() if settings.TEAMS_WEBHOOK_URL else None
        if not self.webhook_url:
            logger.warning("TEAMS_WEBHOOK_URL is not set. Teams notifications will fail.")

    def send(self, title: str, message: str, url: str, category: str = "General") -> bool:
        if not self.webhook_url:
            logger.error("Cannot send Teams notification: Webhook URL missing.")
            return False

        # Emoji logic
        emoji = "📢" 
        if "security" in category.lower(): emoji = "🛡️"

        # Teams requires a specific JSON card format (MessageCard or AdaptiveCard)
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": title,
            "sections": [{
                "activityTitle": f"{emoji} {category}: {title}",
                "activitySubtitle": "AWS-Brief Intelligence",
                "text": message,
                "potentialAction": [{
                    "@type": "OpenUri",
                    "name": "Read Full Story",
                    "targets": [{"os": "default", "uri": url}]
                }]
            }]
        }

        try:
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            # Teams returns 200 OK with body '1' on success
            response.raise_for_status()
            logger.info(f"Teams notification sent for: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")
            return False
