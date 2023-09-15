import time
from threading import Lock
from app_initializer import AppInitializer
from app_initializer.config import RMQConfig
from flask_socketio import SocketIO, emit
import subprocess

import pydevd_pycharm

app = AppInitializer(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
thread = None
thread_lock = Lock()


def get_log_file():
    return app.config["LOG_DIR"] + '/' + RMQConfig.config['LOG_FILES']['CONSUMER']


def read_logs():
    # pydevd_pycharm.settrace('host.docker.internal', port=21001, stdoutToServer=True, stderrToServer=True)
    log_file = get_log_file()
    process = subprocess.Popen(['tail', '-n', '100', '-f', log_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True)

    while True:
        line = process.stdout.readline()
        if not line:
            break
        yield line.strip()


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    lines = []
    timer_start = time.time()

    for line in read_logs():
        socketio.sleep(1)  # Adjust the sleep time as needed
        count += 1
        lines.append(line)
        timer_elapsed = time.time() - timer_start
        if count > 100 or timer_elapsed >= 5:
            socketio.emit('log_update', {'log_line': lines, 'count': count})
            timer_start = time.time()
            lines = []
            count = 0


# WebSocket handler
@socketio.on('connect')
def handle_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

    message = "Connected.... logging from {}".format(get_log_file())
    emit('log_update', {'log_line': message, 'count': 0})
