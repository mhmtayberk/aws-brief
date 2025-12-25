import logging
import requests
import json
from .base import BaseNotifier
from src.utils.config import settings

logger = logging.getLogger(__name__)

class SlackNotifier(BaseNotifier):
    """
    Notifier for Slack using Incoming Webhooks.
    """
    def __init__(self):
        self.webhook_url = settings.SLACK_WEBHOOK_URL.get_secret_value() if settings.SLACK_WEBHOOK_URL else None
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL is not set. Slack notifications will fail.")

    def send(self, title: str, message: str, url: str, category: str = "General") -> bool:
        if not self.webhook_url:
            logger.error("Cannot send Slack notification: Webhook URL missing.")
            return False

        # Emoji mapper based on category keywords
        emoji = "📢" 
        cat_lower = category.lower()
        if "security" in cat_lower: emoji = "🛡️"
        elif "database" in cat_lower: emoji = "🗄️"
        elif "compute" in cat_lower or "serverless" in cat_lower: emoji = "⚡"
        elif "container" in cat_lower: emoji = "📦"
        elif "ai" in cat_lower or "machine learning" in cat_lower: emoji = "🤖"
        elif "cost" in cat_lower: emoji = "💰"
        elif "architecture" in cat_lower: emoji = "🏗️"

        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} {category}: {title[:70]}", # Header + Category
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<{url}|Read full story>"
                    }
                },
                {
                    "type": "divider"
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
            logger.info(f"Slack notification sent for: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
