from .service import NotificationService
from rmq.config import RMQConfig
from utils.func import log


class NotificationManager:
    def __init__(self):
        self.services = []

    def add_service(self, service):
        if isinstance(service, NotificationService):
            self.services.append(service)
        else:
            raise ValueError("Invalid service. It must be a subclass of NotificationService.")

    def send_notifications(self, subject=None, body=None, body_prefix='', service_name=None, command = None):
        for service in self.services:
            if service_name and service.name != service_name:
                continue

            global_ip = RMQConfig.get_global_ip()

            body_prefix += f'\n[{global_ip}][{RMQConfig.config["APP"]["ENV"]}]'
            service.send_notification(subject, body, body_prefix, command)
            log(f'Sent notification to {service.name}')
