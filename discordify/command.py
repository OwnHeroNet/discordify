import signal
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import timedelta
from os import close, getpgid, getpid

import discordify.utils as utils
from discordify.mode import Mode
from discordify.data import Data
from discordify.payload import Payload
from psutil import virtual_memory


class Command:

    def __init__(self, config, args):
        self.__config = config
        self.__args = args
        self.__process = None
        self.__stdin_thread = None
        self.__stdout_thread = None
        self.__stderr_thread = None
        self.__start_time = 0
        self.__end_time = 0
        self.__terminate = False
        self.__stdin_buffer = deque(maxlen=config.buffer_size)
        self.__stdout_buffer = deque(maxlen=config.buffer_size)
        self.__stderr_buffer = deque(maxlen=config.buffer_size)
        self.__stdin_lines = 0
        self.__stdout_lines = 0
        self.__stderr_lines = 0
        self.__cpu_usage = deque(maxlen=100)
        self.__period_timer = None
        self.__timeout_timer = None
        self.__mode = Mode.SINK

    def run(self):
        self.__start_time = time.time()

        if self.__args:
            self.__process = subprocess.Popen(self.__args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            self.__stdin_thread = threading.Thread(target=self.__process_stdin, name='STDIN')
            self.__stdout_thread = threading.Thread(target=self.__process_stdout, name='STDOUT')
            self.__stderr_thread = threading.Thread(target=self.__process_stderr, name='STDERR')
            self.__stdin_thread.start()
            self.__stdout_thread.start()
            self.__stderr_thread.start()
        elif not sys.stdin.isatty():
            self.__stdin_thread = threading.Thread(target=self.__process_stdin, name='STDIN')
            self.__stdin_thread.start()

        # register SIGUSR1 to force a periodic report.
        signal.signal(signal.SIGUSR1, self.__handle_signal)
        signal.signal(signal.SIGPIPE, self.__shutdown)

        if self.__config.period:
            self.__period_timer = threading.Timer(self.__config.period, self.__handle_period)
            self.__period_timer.start()

        if self.__config.timeout:
            self.__timeout_timer = threading.Timer(self.__config.timeout, self.__handle_timeout)
            self.__timeout_timer.start()

    def __process_stdin(self):
        try:
            if not sys.stdin.isatty():
                for line in sys.stdin:
                    if self.__terminate or self.__args and self.__process.poll():
                        break
                    self.__stdin_buffer.append(str(line))
                    self.__stdin_lines += 1
                    if self.__args:
                        self.__process.stdin.write(bytes(line, 'utf-8'))
                    else:
                        sys.stdout.write(line)
                if self.__args:
                    self.__process.stdin.close()
        except BrokenPipeError:
            pass

    def __process_stdout(self):
        with self.__process.stdout as output:
            for line in iter(output.readline, b''):
                self.__stdout_buffer.append(str(line, 'utf-8'))
                self.__stdout_lines += 1
                sys.stdout.write(str(line, 'utf-8'))

    def __process_stderr(self):
        with self.__process.stderr as output:
            for line in iter(output.readline, b''):
                self.__stderr_buffer.append(str(line, 'utf-8'))
                self.__stderr_lines += 1
                sys.stderr.write(str(line, 'utf-8'))

    def __stop_threads(self):
        for timer in [self.__period_timer, self.__timeout_timer]:
            if timer:
                timer.cancel()

        for thread in [self.__stdin_thread, self.__stdout_thread, self.__stderr_thread]:
            try:
                if thread:
                    thread.join(10)
            except TimeoutError:
                pass

    def __monitor(self):
        while not self.__terminate:
            self.__cpu_usage.append(utils.cpu_percent())

    def __prep_buffer(self, buffer):
        return ''.join([(lambda x: x[:50])(x) for x in buffer])

    def wait(self, timeout=None):
        if self.__args:
            self.__process.wait(timeout=timeout)
        else:
            self.__stdin_thread.join()

        self.__terminate = True
        self.__end_time = time.time()
        self.__stop_threads()

        self.report()

    def report(self):
        payload = Payload.create(self.__config, self.data)
        payload.emit_final()

    @property
    def data(self):
        return Data(arguments=self.__args,
                    pid=self.__process.pid if self.__args else getpgid(0),
                    start_time=self.__start_time,
                    end_time=self.__end_time,
                    mode=self.__mode,
                    returncode=self.__process.returncode if self.__args else 0,
                    stdin_lines=self.__stdin_lines,
                    stdout_lines=self.__stdout_lines,
                    stderr_lines=self.__stderr_lines,
                    stdin_buffer=self.__prep_buffer(self.__stdin_buffer),
                    stdout_buffer=self.__prep_buffer(self.__stdout_buffer),
                    stderr_buffer=self.__prep_buffer(self.__stderr_buffer))

    def __handle_period(self):
        if self.__period_timer:
            self.__period_timer.cancel()

        payload = Payload.create(self.__config, self.data)
        payload.emit_period()

        if not self.__terminate:
            self.__period_timer = threading.Timer(self.__config.period, self.__handle_period)
            self.__period_timer.start()

    def __handle_signal(self, *args):
        payload = Payload.create(self.__config, self.data)
        payload.emit_signal()

    def __handle_timeout(self):
        assert self.__timeout_timer
        self.__shutdown()

        payload = Payload.create(self.__config, self.data)
        payload.emit_timeout()

    def handle_interrupt(self):
        self.__shutdown()
        payload = Payload.create(self.__config, self.data)
        payload.emit_interrupt()

    def kill(self):
        assert self.__process != None
        self.__process.kill()
        self.__stop_threads()

    def terminate(self):
        assert self.__process != None
        self.__process.terminate()
        self.__stop_threads()

    def __shutdown(self):
        self.__terminate = True
        self.__end_time = time.time()
        if self.__process:
            self.terminate()
            if not self.__process.poll():
                self.kill()

        close(0)
