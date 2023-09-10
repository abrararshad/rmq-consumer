from notification.service import NotificationService
from .mail import send_log_email


class LogEmailService(NotificationService):
    def __init__(self):
        self.name = 'log_email'

    def send_notification(self, subject=None, body=None, body_prefix=None, command = None):
        send_log_email(subject, body, body_prefix, command)
