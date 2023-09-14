import time
import calendar
import yaml
from flask import current_app
import hashlib
from multiprocessing import current_process
from rmq.config import RMQConfig
import traceback


def cal_timestamp(time_from=None):
    if not time_from:
        time_from = time.gmtime()

    return calendar.timegm(time_from)


def load_yaml(path):
    with open(path, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def log(msg):
    env = RMQConfig.config['APP']['ENV']
    msg = '[%s]:[%s] %s' % (env, current_process().name, str(msg))
    current_app.logger.info(msg)

    if env == 'local':
        print(msg)


def log_error(msg):
    env = RMQConfig.config['APP']['ENV']
    msg = str(msg) + '. Detail: ' + str(traceback.format_exc())
    error = '[%s]:[%s]: %s' % (env, current_process().name, str(msg))
    current_app.logger.error(error)

    if env == 'local':
        print(msg)


def print_cursor_data(cursor):
    for document in cursor:
        print(document)
        # for key in document:
        #     print(key)


def md5_hash(string):
    return hashlib.md5(string.encode()).hexdigest()
