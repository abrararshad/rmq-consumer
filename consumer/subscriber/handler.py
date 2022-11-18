from utils.func import log, log_error
from rmq.config import RMQConfig
import shlex
import json
from .commandexecutor import CommandExecutor
import pydevd_pycharm


def handle_queue(channel, delivery_tag, body, extra_args):
    # pydevd_pycharm.settrace('172.17.0.1', port=21001, stdoutToServer=True, stderrToServer=True)
    data = body.decode("utf-8")
    try:
        exec_command(data)
    except Exception as e:
        log_error(e)
        reject_job(channel, delivery_tag)
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
        # TODO: May we want to really make sure queue is completely done.
        log('Acknowledging tag:' + str(delivery_tag))
        channel.basic_ack(delivery_tag=delivery_tag)
    except Exception as e:
        log(e)


def reject_job(channel, delivery_tag):
    try:
        log('Rejecting  tag:' + str(delivery_tag))
        channel.basic_reject(delivery_tag=delivery_tag, requeue=False)
    except Exception as e:
        log(e)
