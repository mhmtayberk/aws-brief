from typing import List
from .base import BaseNotifier
from .slack import SlackNotifier
from .email import EmailNotifier
from .teams import TeamsNotifier
from .discord import DiscordNotifier

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
        return notifiers
