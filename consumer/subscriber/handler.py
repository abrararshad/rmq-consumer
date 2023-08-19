import os
from rmq.config import RMQConfig
from utils.func import log, log_error
from rmq.config import RMQConfig
import shlex
import json
from consumer.rabbitmq.rabbitmq_base import RabbitMQRejectionThresholdError, error_queue
from .commandexecutor import CommandExecutor
import pydevd_pycharm

CONSECUTIVE_REJECTIONS_THRESHOLD = 3
consecutive_rejections = 0


def get_logs_dir():
    return RMQConfig.config['APP_LOGS_DIR']


def get_job_rejections():
    filename = f"{get_logs_dir()}/job_rejections.txt"

    if not os.path.exists(filename):
        set_job_rejections(consecutive_rejections)

    with open(filename, "r") as file:
        return int(file.read())


def set_job_rejections(count):
    filename = f"{get_logs_dir()}/job_rejections.txt"
    with open(filename, "w") as file:
        file.write(str(count))


def handle_queue(channel, delivery_tag, body, extra_args):
    # pydevd_pycharm.settrace('host.docker.internal', port=21001, stdoutToServer=True, stderrToServer=True)
    global consecutive_rejections

    data = body.decode("utf-8")
    try:
        exec_command(data)
        # set_job_rejections(0)
        error_queue.empty()
    except Exception as e:
        log_error(e)
        reject_job(channel, delivery_tag)

        error_queue.put(str(e))

        # consecutive_rejections += 1
        # total_rejections = get_job_rejections() + 1
        # set_job_rejections(total_rejections)
        # log(f'total consecutive rejections: {total_rejections}')
        # if total_rejections >= CONSECUTIVE_REJECTIONS_THRESHOLD:
        #     error_msg = f'Exceeded consecutive rejections threshold of {CONSECUTIVE_REJECTIONS_THRESHOLD}'
        #     log_error(error_msg)
        #     raise RabbitMQRejectionThresholdError(error_msg)

        exit_process()
        return

    acknowledge_job(channel, delivery_tag)
    exit_process()


def exit_process():
    log('exiting...')
    exit(0)


def exec_command(data):
    if not data:
        return None

    cwd = RMQConfig.consumer_value('CWD')
    command = RMQConfig.consumer_value('COMMAND')
    command = "{} '{}'".format(command, data)
    log("Running command: {} in {}".format(command, cwd))
    executor = CommandExecutor()

    # log output to the file
    log_file = open('{}/{}'.format(RMQConfig.config['APP_LOGS_DIR'], RMQConfig.config['APP']['APP_LOG_NAME']), "a")
    with executor.run(command=command, c_progress=None, c_stderr=log_file, c_stdout=log_file, cwd=cwd) as process:
        process.communicate()


def progress_output(line):
    if line:
        print(line)


def acknowledge_job(channel, delivery_tag):
    try:
        # Now acknowledge the queue's message for broker to delete it.
        # TODO: We may really want to make sure queue is completely done.
        log('Acknowledging tag:' + str(delivery_tag))
        channel.basic_ack(delivery_tag=delivery_tag)
    except Exception as e:
        log(e)


def reject_job(channel, delivery_tag):
    try:
        log('Rejecting  tag:' + str(delivery_tag))
        channel.basic_reject(delivery_tag=delivery_tag, requeue=True)
    except Exception as e:
        log(e)
