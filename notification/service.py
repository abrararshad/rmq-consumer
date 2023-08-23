class NotificationService:
    name = None

    def send_notification(self, subject=None, body=None, body_prefix=None):
        raise NotImplementedError("Subclasses must implement send_notification")
