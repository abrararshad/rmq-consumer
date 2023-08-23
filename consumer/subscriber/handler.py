import os
from utils.func import log, log_error
from rmq.config import RMQConfig
from consumer.rabbitmq.rabbitmq_base import error_queue
from .commandexecutor import CommandExecutor
from notification import notification_manager
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
    command, cwd = prepare_command(data)
    try:
        log("Running command: {} in {}".format(command, cwd))
        exec_command(command, cwd)
        # set_job_rejections(0)
        error_queue.empty()
    except Exception as e:
        log_error(e)
        reject_job(channel, delivery_tag)

        error = str(e)
        error_queue.put(error)

        error_body = f'Running command: {command}   in   {cwd} \n\n Failed with error: {error}'
        notification_manager.send_notifications(subject='Error in consumer', body=error_body, service_name='discord')
        exit_process()
        return

    acknowledge_job(channel, delivery_tag)
    exit_process()


def exit_process():
    log('exiting...')
    exit(0)


def prepare_command(data):
    if not data:
        return None

    cwd = RMQConfig.consumer_value('CWD')
    command = RMQConfig.consumer_value('COMMAND')
    command = "{} '{}'".format(command, data)
    return command, cwd


def exec_command(command, cwd):
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
