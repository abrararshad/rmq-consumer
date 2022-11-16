import time
from consumer.rabbitmq.queue_subscriber import QueueSubscriber
from utils.func import log, log_error
from .handler import handle_queue

import pydevd_pycharm


# pydevd_pycharm.settrace('172.17.0.1', port=21001, stdoutToServer=True, stderrToServer=True)


def connect():
    try:
        queue_subscriber = QueueSubscriber(logger=log)
        queue_subscriber.subscribe(callback=handle_queue, with_pool=False)
    except Exception as e:
        log_error(e)
    finally:
        connect_back_in = 5
        log("Reconnecting after {} seconds".format(connect_back_in))
        time.sleep(connect_back_in)
        connect()

    exit()
