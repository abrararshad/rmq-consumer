from .rabbitmq_base import RabbitMQBase


class QueueSender(RabbitMQBase):
    role_type = 'sender'
