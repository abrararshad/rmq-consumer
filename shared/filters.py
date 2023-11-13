from flask import current_app
from datetime import datetime
import json
import time
from datetime import datetime


@current_app.template_filter('ctime')
def timectime(s):
    return time.ctime(s)


@current_app.template_filter('time_ago')
def time_ago(s):
    """
    Convert a timestamp into a 'time ago' format.
    """
    now = datetime.now()
    timestamp = datetime.fromtimestamp(s)
    diff = now - timestamp
    seconds = diff.total_seconds()

    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds // 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    else:
        return f"{int(seconds // 86400)} days ago"


@current_app.template_filter('print_vars')
def print_vars(obj):
    return dir(obj)


@current_app.template_filter('pretty_json')
def pretty_json(data):
    return json.dumps(data, indent=4)


@current_app.template_filter('pretty_date')
def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " secs"
        if second_diff < 120:
            return "a min"
        if second_diff < 3600:
            return str(int(second_diff / 60)) + " mins"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(int(second_diff / 3600)) + " hrs ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(int(day_diff)) + " days ago"
    if day_diff < 31:
        return str(int(day_diff / 7)) + " weeks ago"
    if day_diff < 365:
        return str(int(day_diff / 30)) + " months ago"
    return str(int(day_diff / 365)) + " years ago"

# jinja2.filters.FILTERS['print_vars'] = print_vars
