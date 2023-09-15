import json
import re
from flask import render_template, current_app, Response, redirect, request, jsonify
from shared.services import JobService
from shared.models.job import Job
from pymongo.errors import OperationFailure
from utils.func import log_error
import subprocess
import pydevd_pycharm


# pydevd_pycharm.settrace('host.docker.internal', port=21001, stdoutToServer=True, stderrToServer=True)

@current_app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')  # Get the user's dot-notation query from the request

    # Split the query by 'AND' to handle multiple conditions
    conditions = query.split(' AND ')

    # Build a MongoDB query using dot notation for each condition
    mongo_query = {}
    for condition in conditions:
        operator = None
        key = None
        if condition.count(':') == 2:
            key, operator, value = condition.split(':')
        elif condition.count(':') == 1:
            key, value = condition.split(':')

        if not key:
            return render_template('jobs.html', jobs={}, error='The query is incorrect')

        keys = key.split('.')

        if len(keys) == 1:
            last_key = keys[0]

            job = Job(None)
            try:
                value = job.convert_value_by_field_type(last_key, value)
            except Exception as ex:
                error = f'The field {last_key} is incorrect or probably it is not at the root level'
                return render_template('jobs.html', jobs={}, error=error)

        else:
            if re.match(r'^\d+$', value):
                value = int(value)

        if operator:
            if operator == '$in' or operator == '$nin':
                value = value.split(',')
            mongo_query[key] = {operator: value}
        else:
            mongo_query[key] = value

        results = JobService._collection.find(mongo_query)
        result_list = list(results)

        return render_template('jobs.html', jobs=result_list)


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
