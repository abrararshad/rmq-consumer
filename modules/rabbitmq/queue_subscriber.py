from .rabbitmq_base import RabbitMQBase


class QueueSubscriber(RabbitMQBase):
    role_type = 'subscriber'
