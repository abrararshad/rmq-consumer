from notification.service import NotificationService
from discordwebhook import Discord


class DiscordService(NotificationService):
    def __init__(self, webhook_url):
        self.name = 'discord'
        self.discord = Discord(url=webhook_url)

    def send_notification(self, subject=None, body=None, body_prefix=None):
        message = f'{subject}\n{body_prefix}\n{body}\n------------------\n'
        self.discord.post(content=message)
