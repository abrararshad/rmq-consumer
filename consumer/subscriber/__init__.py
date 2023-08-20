import time
from consumer.rabbitmq.queue_subscriber import QueueSubscriber
from consumer.rabbitmq.rabbitmq_base import RabbitMQRejectionThresholdError
from utils.func import log, log_error
from .handler import handle_queue
from consumer.mail import send_log_email
import pydevd_pycharm

MAX_RETRY = 30
RETRY_DELAY = 5
RETRY_BACKOFF_FACTOR = 2


def connect():
    # pydevd_pycharm.settrace('host.docker.internal', port=21001, stdoutToServer=True, stderrToServer=True)
    retry_count = 0

    while retry_count < MAX_RETRY:
        try:
            queue_subscriber = QueueSubscriber(logger=log)
            queue_subscriber.subscribe(callback=handle_queue, with_pool=False)
            return  # Successful connection, exit loop
        except Exception as e:
            log_error(e)
            last_error = e

        if isinstance(last_error, RabbitMQRejectionThresholdError):
            log(f'Not connecting again. {str(last_error)}')
            send_email()
            exit()

        retry_count += 1
        if retry_count < MAX_RETRY:
            wait_time = RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** retry_count)
            log("Reconnecting after {} seconds".format(wait_time))
            time.sleep(wait_time)

        log("Max retry limit reached. Exiting...")
        exit()


def send_email():
    send_log_email()
