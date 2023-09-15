import time
from apps.consumer.rabbitmq.queue_subscriber import QueueSubscriber
from apps.consumer.rabbitmq.rabbitmq_base import RabbitMQRejectionThresholdError, error_queue, ERRORS_THRESHOLD_LIMIT
from utils.func import log, log_error
from .handler import handle_queue
from app_initializer.config import RMQConfig
from notification import notification_manager

MAX_RETRY = 3
RETRY_DELAY = 5
RETRY_BACKOFF_FACTOR = 2


def connect():
    # pydevd_pycharm.settrace('host.docker.internal', port=21001, stdoutToServer=True, stderrToServer=True)
    global MAX_RETRY, RETRY_DELAY, RETRY_BACKOFF_FACTOR

    consumer_config = RMQConfig.consumer_value()

    if 'RETRY' in consumer_config:
        retry_config = consumer_config['RETRY']
        if retry_config['MAX_RETRY']:
            MAX_RETRY = retry_config['MAX_RETRY']

        if retry_config['RETRY_DELAY']:
            RETRY_DELAY = retry_config['RETRY_DELAY']

        if retry_config['RETRY_BACKOFF_FACTOR']:
            RETRY_BACKOFF_FACTOR = retry_config['RETRY_BACKOFF_FACTOR']

    retry_count = 0

    while retry_count < MAX_RETRY:
        try:
            queue_subscriber = QueueSubscriber(logger=log)
            queue_subscriber.subscribe(callback=handle_queue, with_pool=False)
            return  # Successful connection, exit loop
        except Exception as e:
            log_error(e)
            last_error = e
            notification_manager.send_notifications(f'Error connecting to RabbitMQ: {str(e)}', service_name='discord')

        if isinstance(last_error, RabbitMQRejectionThresholdError):
            log(f'Not connecting again. {str(last_error)}')
            send_threshold_reached_email()

        retry_count += 1
        if retry_count < MAX_RETRY:
            wait_time = RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** retry_count)
            log("Reconnecting after {} seconds, remaining attempts are {}".format(wait_time, MAX_RETRY - retry_count))
            time.sleep(wait_time)

    if retry_count >= MAX_RETRY:
        log("Max retry limit reached. Exiting...")
        send_max_tried_failed_email()
        exit()


def send_threshold_reached_email():
    logs_lines = []
    while not error_queue.empty():
        logs_lines.append(error_queue.get())

    body_prefix = f'<h3>Threshold limit: {ERRORS_THRESHOLD_LIMIT}</h3>'
    notification_manager.send_notifications(body=logs_lines, body_prefix=body_prefix, service_name='log_email')


def send_max_tried_failed_email():
    body_prefix = f'<h3>Max retry limit reached: {MAX_RETRY}</h3>'
    notification_manager.send_notifications(body_prefix=body_prefix, service_name='log_email')
