from shared.models.job import Job
from shared.services import JobService
import subprocess
import re


def process_condition(condition):
    operator = None
    key = None
    if condition.count(':') == 2:
        key, operator, value = condition.split(':')
    elif condition.count(':') == 1:
        key, value = condition.split(':')
    return key, operator, value


def prepare_mongo_query(conditions):
    mongo_query = {}
    for condition in conditions:
        key, operator, value = process_condition(condition)
        if not key:
            raise Exception('The query is incorrect')

        # Assuming Job and JobService are defined earlier
        if '.' not in key:
            job = Job(JobService._collection)
            try:
                value = job.convert_value_by_field_type(key, value)
            except Exception as ex:
                raise Exception(f'The field {key} is incorrect or probably it is not at the root level')
        else:
            if re.match(r'^\d+$', value):
                value = int(value)

        if operator:
            if operator in ['$in', '$nin']:
                value = value.split(',')
            mongo_query[key] = {operator: value}
        else:
            mongo_query[key] = value
    return mongo_query


def search_jobs(query=None, page=1, page_size=10):
    if query:
        conditions = query.split(' AND ')
        mongo_query = prepare_mongo_query(conditions)
    else:
        mongo_query = {}

    total_cursor = JobService._collection.find(mongo_query).sort("created", -1)

    # Clone the cursor for paginated results and apply limit and skip
    results_cursor = total_cursor.clone()
    results_cursor = results_cursor.skip((page - 1) * page_size).limit(page_size)

    return (mongo_query, total_cursor, results_cursor)


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