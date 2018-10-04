import subprocess
import sys
import threading
import time
from collections import deque
from datetime import timedelta

from payload import Payload


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
        self.__stdin_buffer = deque(maxlen=5)
        self.__stdout_buffer = deque(maxlen=5)
        self.__stderr_buffer = deque(maxlen=5)
        self.__stdin_lines = 0
        self.__stdout_lines = 0
        self.__stderr_lines = 0

    def run(self):
        self.__start_time = time.time()
        self.__process = subprocess.Popen(self.__args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        self.__stdin_thread = threading.Thread(target=self.__process_stdin, name='STDIN')
        self.__stdout_thread = threading.Thread(target=self.__process_stdout, name='STDOUT')
        self.__stderr_thread = threading.Thread(target=self.__process_stderr, name='STDERR')
        self.__stdin_thread.start()
        self.__stdout_thread.start()
        self.__stderr_thread.start()

    def __process_stdin(self):
        if not sys.stdin.isatty():
            for line in sys.stdin:
                if self.__process.poll() or self.__terminate:
                    break
                self.__stdin_buffer.append(str(line))
                self.__stdin_lines += 1
                self.__process.stdin.write(bytes(line, 'utf-8'))
            self.__process.stdin.close()

    def __process_stdout(self):
        with self.__process.stdout as output:
            for line in iter(output.readline, b''):
                self.__stdout_buffer.append(str(line))
                self.__stdout_lines += 1
                sys.stdout.buffer.write(line)

    def __process_stderr(self):
        with self.__process.stderr as output:
            for line in iter(output.readline, b''):
                self.__stderr_buffer.append(str(line))
                self.__stderr_lines += 1
                sys.stderr.buffer.write(line)

    def __stop_threads(self):
        for thread in [self.__stdin_thread, self.__stdout_thread, self.__stderr_thread]:
            try:
                thread.join(10)
            except TimeoutError:
                pass

    def wait(self, timeout=None):
        self.__process.wait(timeout=timeout)
        self.__terminate = True
        self.__end_time = time.time()
        payload = Payload(self.__config)
        payload.prepare(
            cmd=' '.join(self.__args),
            pid=self.__process.pid,
            start=self.__start_time,
            end=self.__end_time,
            returncode=self.__process.returncode,
            stdin_lines=self.__stdin_lines,
            stdout_lines=self.__stdout_lines,
            stderr_lines=self.__stderr_lines,
            stdout_buffer='\n> '.join(self.__stdout_buffer))
        self.__stop_threads()

    def kill(self):
        assert self.__process != None
        self.__process.kill()
        self.__stop_threads()

    def terminate(self):
        assert self.__process != None
        self.__process.terminate()
        self.__stop_threads()