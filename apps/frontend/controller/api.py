import json
from flask import render_template, current_app, Response, redirect, request
from shared.services import JobService
from modules.rabbitmq.queue_sender import QueueSender
from .func import search_jobs, run_command
from utils.func import log_error
import pydevd_pycharm

# pydevd_pycharm.settrace('host.docker.internal', port=21001, stdoutToServer=True, stderrToServer=True)


@current_app.route('/', methods=['GET'], defaults={'page': 1, 'query': ''})
@current_app.route('/<page>', methods=['GET'], defaults={'query': ''})
@current_app.route('/<page>/<query>', methods=['GET'])
def search(page, query):
    if not query:
        query = request.args.get('query')

    if not query:
        query = ''

    page = int(page)

    # remove white spaces from query
    # query = query.replace(" ", "")

    is_searched = False
    total_pages = 0
    total_count = 0
    try:
        page_size = 20
        mongo_query, total_cursor, results_cursor = search_jobs(query, page, page_size)

        result = list(results_cursor)
        total_count = JobService._collection.count_documents(mongo_query)

        total_pages = -(-total_count // page_size)
    except Exception as ex:
        return render_template('search.html', jobs={}, query=query, error=ex, current_page=page, total_pages=total_pages,
                               count=total_count, searched=is_searched)

    if query and len(result) > 0:
        is_searched = True

    return render_template('search.html', jobs=result, query=query, search=True, current_page=page,
                           total_pages=total_pages, count=total_count, searched=is_searched)


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


@current_app.route('/requeue/by_hash/<hash>', methods=['GET'])
def requeue_by_hash(hash):
    '''
    Requeue a specific job by id
    '''

    job = JobService.find_by_hash(hash)

    if not job:
        return redirect(request.referrer or '/')

    try:
        sender = QueueSender()
        sender.send(job.command_args)
    except Exception as ex:
        error_msg = f"An error occurred: {ex}"
        log_error(error_msg)
        return render_template('job.html', job=job, msg=error_msg, msg_type='danger')

    return redirect(request.referrer or '/')


@current_app.route('/requeue/by_query/<exec_query>', methods=['GET'])
def requeue_by_query(exec_query):
    if not exec_query:
        return

    _, __, results_cursor = search_jobs(exec_query, 1, 1000)

    # get all jobs
    jobs = list(results_cursor)

    # args = [job['command_args '] for job in jobs]
    args = []
    for job in jobs:
        args.append(job['command_args'])

    # send command args to queue one by one
    sender = QueueSender()
    for arg in args:
        sender.send(arg)

    return redirect(request.referrer or '/')


@current_app.route('/job/<job_id>/reset/error', methods=['GET'])
def job_reset_error(job_id):
    job = JobService.get(job_id)
    if job:
        job.error = None
        job.save()

    return redirect(request.referrer or '/')

# @current_app.route('/', methods=['GET'])
# def get_jobs():
#     '''
#     Get all jobs grouped by hash, and project fields like try, error, status, etc.
#     '''
#
#     pipeline = [
#         {
#             '$sort': {
#                 'timestamp': -1
#             }
#         },
#         {
#             '$group': {
#                 '_id': '$hash',
#                 'latest_document': {'$first': '$$ROOT'},
#                 'count': {'$sum': 1}
#             }
#         },
#         {
#             '$replaceRoot': {
#                 'newRoot': {
#                     '$mergeObjects': ['$latest_document', {'count': '$count'}]
#                 }
#             }
#         },
#         {
#             '$unset': 'latest_document'  # Remove the latest_document field
#         }
#     ]
#
#     try:
#         jobs = JobService.aggregate(pipeline)
#     except OperationFailure as e:
#         print(f"MongoDB OperationFailure: {e}")
#     except Exception as ex:
#         print(f"An error occurred: {ex}")
#
#     # print_cursor_data(jobs)
#
#     # return the template with jobs data
#     return render_template('search.html', jobs=jobs)
