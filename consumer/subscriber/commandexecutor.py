import shlex
import subprocess
import threading
import logging


def _p_open(commands, cwd, p_stdin=False, p_stdout=False, p_stderr=subprocess.STDOUT, universal_newlines=False):
    stdin_stream = subprocess.PIPE if p_stdin else None
    stdout_stream = subprocess.PIPE if p_stdout else None
    stderr_stream = p_stderr

    p = subprocess.Popen(shlex.split(commands), stdout=stdout_stream, stderr=stderr_stream, stdin=stdin_stream
                         , universal_newlines=universal_newlines, cwd=cwd)

    # p.wait()
    return p


class CommandExecutor(object):
    def __init__(self):
        self.out = None
        self.err = None
        self.c_progress = None
        self.p = None

    def run(self, command, c_progress, cwd, c_stdout=None, c_stderr=None, c_stdin=None):
        self.c_progress = c_progress
        if callable(c_progress):
            self.p = _p_open(command, cwd, c_stdin, True, universal_newlines=True)
        else:
            self.p = _p_open(command, cwd, c_stdin, c_stdout, subprocess.PIPE if c_stderr else False)

        # Clear the previous output and error data
        self.out = None
        self.err = None

        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.p.kill()
        self.p.wait()  # Wait for the subprocess to terminate

    def kill(self):
        self.p.kill()

    def _show_progress(self):
        log = []

        while True:
            line = self.p.stdout.readline().strip()
            if line != '':
                log += [line]

            if line == '' and self.p.poll() is not None:
                break

            self.c_progress(line)

        self.out = log

    def _thread_progress(self, timeout):
        thread = threading.Thread(target=self._show_progress)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            self.p.terminate()
            thread.join()
            error = 'Timeout! exceeded the timeout of {} seconds.'.format(str(timeout))
            logging.error(error)
            raise RuntimeError(error)

    def communicate(self, c_input=None, timeout=None):
        if callable(self.c_progress):
            self._thread_progress(timeout)
        else:
            self.out, self.err = self.p.communicate(c_input)

        if self.p.returncode != 0:
            error = str(self.err) if self.err else str(self.out)
            logging.error('Failed to execute command: {}'.format(error))
            raise RuntimeError('Failed to execute command: ', error)

        logging.info("Executed command successfully")

        return self.out, self.err
