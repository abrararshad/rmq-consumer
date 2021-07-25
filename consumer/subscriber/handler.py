from utils.func import log, log_error
from rmq.config import RMQConfig
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
        raise e

    acknowledge_job(channel, delivery_tag)


def exec_command(data):
    try:
        args = json.loads(data)
    except Exception as e:
        log_error(e)
        return None

    if 'user_id' not in args or 'cl_id' not in args or 'req_id' not in args:
        log_error('Not executing some params maybe missing [user_id, cli_id, req_id]')
        return None

    entities = args['entities'] if 'entities' in args else None

    if entities:
        try:
            entities = json.dumps(entities)
        except Exception as e:
            log_error(e)
            return None

    cwd = RMQConfig.consumer_value('CWD')
    command = RMQConfig.consumer_value('COMMAND')
    command = "{} '{}' '{}' '{}' '{}'".format(command, args['user_id'], args['req_id'], args['cl_id'], entities)

    executor = CommandExecutor()
    with executor.run(command=command, c_progress=None, cwd=cwd) as process:
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
