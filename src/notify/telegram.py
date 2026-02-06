import logging
import requests
from .base import BaseNotifier
from src.utils.config import settings

logger = logging.getLogger(__name__)

class TelegramNotifier(BaseNotifier):
    """
    Notifier for Telegram using Bot API.
    """
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN.get_secret_value() if settings.TELEGRAM_BOT_TOKEN else None
        self.chat_id = settings.TELEGRAM_CHAT_ID
        if not self.bot_token or not self.chat_id:
            logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Telegram notifications will fail.")

    def send(self, title: str, message: str, url: str, category: str = "General") -> bool:
        if not self.bot_token or not self.chat_id:
            logger.error("Cannot send Telegram notification: Credentials missing.")
            return False

        emoji = "📢"
        cat_lower = category.lower()
        if "security" in cat_lower: emoji = "🛡️"
        elif "database" in cat_lower: emoji = "🗄️"
        elif "compute" in cat_lower or "serverless" in cat_lower: emoji = "⚡"
        elif "container" in cat_lower: emoji = "📦"
        elif "ai" in cat_lower or "machine learning" in cat_lower: emoji = "🤖"
        elif "cost" in cat_lower: emoji = "💰"
        elif "architecture" in cat_lower: emoji = "🏗️"

        text = f"{emoji} *{category}*: {title}\n\n{message}\n\n[Read More]({url})"

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Telegram notification sent for: {title}")
            return True
        except requests.RequestException as e:
            logger.error(f"Telegram API request failed: {e}")
            return False
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid Telegram payload: {e}")
            return False
