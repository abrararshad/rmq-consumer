from rmq.config import RMQConfig
from utils.func import log_error
from notification.manager import NotificationManager
from .services.discord import DiscordService
from .services.log_mail import LogEmailService

notification_manager = NotificationManager()

# Discord
discord_webhook_url = RMQConfig.notification_value()['DISCORD']['WEBHOOK_URL']
if discord_webhook_url:
    discord_service = DiscordService(discord_webhook_url)
    notification_manager.add_service(discord_service)
else:
    log_error('Discord webhook url not found. Discord notifications will not be sent.')

# Log email service
log_email_service = LogEmailService()
notification_manager.add_service(log_email_service)
