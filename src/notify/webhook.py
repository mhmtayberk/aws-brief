import logging
import requests
import hashlib
import hmac
import json
from datetime import datetime
from .base import BaseNotifier
from src.utils.config import settings

logger = logging.getLogger(__name__)

class WebhookNotifier(BaseNotifier):
    """
    Generic webhook notifier with optional HMAC signature support.
    Sends notifications to any HTTP endpoint.
    """
    def __init__(self):
        self.webhook_url = settings.WEBHOOK_URL
        self.webhook_secret = settings.WEBHOOK_SECRET.get_secret_value() if settings.WEBHOOK_SECRET else None
        
        if not self.webhook_url:
            logger.warning("WEBHOOK_URL not set. Webhook notifications will fail.")
    
    def send(self, title: str, message: str, url: str, category: str = "General") -> bool:
        """
        Send notification to webhook endpoint.
        
        Args:
            title: Notification title
            message: Notification message
            url: Source URL
            category: Category/tag
            
        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            logger.error("Cannot send webhook: WEBHOOK_URL not configured")
            return False
        
        payload = {
            "title": title,
            "message": message,
            "url": url,
            "category": category,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        headers = {"Content-Type": "application/json"}
        
        # Add HMAC signature if secret is configured
        if self.webhook_secret:
            signature = hmac.new(
                self.webhook_secret.encode(),
                json.dumps(payload, sort_keys=True).encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"
            logger.debug("HMAC signature added to webhook request")
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Webhook notification sent: {title}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Webhook request failed: {e}")
            return False
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Invalid webhook payload: {e}")
            return False
