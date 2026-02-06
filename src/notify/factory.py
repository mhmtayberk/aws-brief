from typing import List
from .base import BaseNotifier
from .slack import SlackNotifier
from .email import EmailNotifier
from .teams import TeamsNotifier
from .discord import DiscordNotifier
from .telegram import TelegramNotifier
from .webhook import WebhookNotifier
from .mattermost import MattermostNotifier

class NotificationFactory:
    """
    Factory to get enabled notifiers.
    """
    @staticmethod
    def get_notifiers(channels: List[str] = ["slack"]) -> List[BaseNotifier]:
        notifiers = []
        for channel in channels:
            if channel.lower() == "slack":
                notifiers.append(SlackNotifier())
            elif channel.lower() == "email":
                notifiers.append(EmailNotifier())
            elif channel.lower() == "teams":
                notifiers.append(TeamsNotifier())
            elif channel.lower() == "discord":
                notifiers.append(DiscordNotifier())
            elif channel.lower() == "telegram":
                notifiers.append(TelegramNotifier())
            elif channel.lower() == "webhook":
                notifiers.append(WebhookNotifier())
            elif channel.lower() == "mattermost":
                notifiers.append(MattermostNotifier())
        return notifiers
