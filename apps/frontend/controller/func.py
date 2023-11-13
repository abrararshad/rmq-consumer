from shared.models.job import Job
from shared.services import JobService
import subprocess
import re


def process_condition(condition):
    operator = None
    value = None
    if condition.count(':') == 2:
        key, operator, value = condition.split(':')
    elif condition.count(':') == 1:
        key, value = condition.split(':')
    return key.strip(), operator, value.strip()


def prepare_mongo_query(query):
    # Split the query by spaces while respecting quoted strings
    parts = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', query)
    mongo_query = []
    temp_query = {}

    for part in parts:
        if part in ['AND', 'OR']:
            if temp_query:
                mongo_query.append(temp_query)
                temp_query = {}
            mongo_query.append(part)
        else:
            key, operator, value = process_condition(part)
            if not key:
                raise Exception('The query is incorrect')

            # ... [Your existing code to process the condition] ...

            query_part = {key: {operator: value}} if operator else {key: value}
            temp_query.update(query_part)

    # Add the last condition if present
    if temp_query:
        mongo_query.append(temp_query)

    # Convert to MongoDB $and/$or structure
    return construct_mongo_logical_query(mongo_query)


def construct_mongo_logical_query(query_parts):
    if not query_parts:
        return {}

    if len(query_parts) == 1:
        return query_parts[0]

    mongo_query = {"$or": []}
    and_conditions = []

    for part in query_parts:
        if part == 'AND':
            continue
        elif part == 'OR':
            if and_conditions:
                mongo_query["$or"].append({"$and": and_conditions})
                and_conditions = []
        else:  # part is a condition
            and_conditions.append(part)

    if and_conditions:
        # Handle the case where the query ends with AND conditions
        if len(mongo_query["$or"]) == 0:
            # If there are no OR conditions, return the AND conditions directly
            return {"$and": and_conditions}
        else:
            # Add the remaining AND conditions
            mongo_query["$or"].append({"$and": and_conditions})

    return mongo_query if mongo_query["$or"] else {"$and": and_conditions}


def search_jobs(query=None, page=1, page_size=10):
    if query:
        mongo_query = prepare_mongo_query(query)
    else:
        mongo_query = {}

    # ... [Your existing code to query MongoDB and handle pagination] ...
    total_cursor = JobService._collection.find(mongo_query).sort("created", -1)
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
