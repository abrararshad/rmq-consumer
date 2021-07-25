import time
from consumer.rabbitmq.queue_subscriber import QueueSubscriber
from utils.func import log, log_error
from .handler import handle_queue

import pydevd_pycharm


# pydevd_pycharm.settrace('172.17.0.1', port=21001, stdoutToServer=True, stderrToServer=True)


def connect():
    queue_subscriber = None
    try:
        queue_subscriber = QueueSubscriber()
        queue_subscriber.subscribe(handle_queue, True)
    except Exception as e:
        log_error(e)
        if queue_subscriber:
            queue_subscriber.clear_cache()
    finally:
        connect_back_in = 5
        log("Reconnecting after {} seconds".format(connect_back_in))
        time.sleep(connect_back_in)
        connect()

    exit()
