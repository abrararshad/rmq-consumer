import json
from flask import render_template, current_app, Response, redirect, request
from shared.services import JobService
from pymongo.errors import OperationFailure
from utils.func import log_error
import subprocess
import pydevd_pycharm


# pydevd_pycharm.settrace('host.docker.internal', port=21001, stdoutToServer=True, stderrToServer=True)


@current_app.route('/', methods=['GET'])
def get_jobs():
    '''
    Get all jobs grouped by hash, and project fields like try, error, status, etc.
    '''

    pipeline = [
        {
            '$sort': {
                'timestamp': -1
            }
        },
        {
            '$group': {
                '_id': '$hash',
                'latest_document': {'$first': '$$ROOT'},
                'count': {'$sum': 1}
            }
        },
        {
            '$replaceRoot': {
                'newRoot': {
                    '$mergeObjects': ['$latest_document', {'count': '$count'}]
                }
            }
        },
        {
            '$unset': 'latest_document'  # Remove the latest_document field
        }
    ]

    try:
        jobs = JobService.aggregate(pipeline)
    except OperationFailure as e:
        print(f"MongoDB OperationFailure: {e}")
    except Exception as ex:
        print(f"An error occurred: {ex}")

    # print_cursor_data(jobs)

    # return the template with jobs data
    return render_template('jobs.html', jobs=jobs)


@current_app.route('/job/<hash>', methods=['GET'])
def get_job(hash):
    '''
    Get a specific job by id
    '''

    job = JobService.find_by_hash(hash)

    return render_template('job.html', job=job)


@current_app.route('/job/<hash>/run', methods=['GET'])
def run_job(hash):
    '''
    Run a specific job by id
    '''

    job = JobService.find_by_hash(hash)

    if not job:
        return redirect(request.referrer or '/')

    try:
        command = json.dumps(job.command_args)
    except Exception as ex:
        log_error(f"An error occurred: {ex}")
        raise Exception(f"An error occurred: {ex}")

    if not command:
        raise Exception(f"Command is empty for job {job.id}")

    command = "{} '{}'".format(job.executor, command)
    return Response(run_command(command, job.cwd), mimetype='text/html')


def run_command(command, cwd):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        shell=True,
        cwd=cwd
    )

    for line in process.stdout:
        yield line.strip() + '<br/>'
