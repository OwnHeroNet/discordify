import subprocess
import sys
import threading
import time
from collections import deque
from datetime import timedelta
from os import getpgid

from discordify.payload import Payload


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
        for thread in [self.__stdin_thread, self.__stdout_thread, self.__stderr_thread]:
            try:
                if thread:
                    thread.join(10)
            except TimeoutError:
                pass

    def __prep_buffer(self, buffer):
        return ''.join([(lambda x: x[:50])(x) for x in buffer])

    def wait(self, timeout=None):
        if self.__args:
            self.__process.wait(timeout=timeout)
        else:
            self.__stdin_thread.join()

        self.__terminate = True
        self.__end_time = time.time()
        payload = Payload(self.__config)
        payload.prepare(
            cmd=self.__args if self.__args else ['<discordify>'],
            pid=self.__process.pid if self.__args else getpgid(0),
            start=self.__start_time,
            end=self.__end_time,
            returncode=self.__process.returncode if self.__args else 0,
            stdin_lines=self.__stdin_lines,
            stdout_lines=self.__stdout_lines,
            stderr_lines=self.__stderr_lines,
            stdin_buffer=self.__prep_buffer(self.__stdin_buffer),
            stdout_buffer=self.__prep_buffer(self.__stdout_buffer),
            stderr_buffer=self.__prep_buffer(self.__stderr_buffer))
        self.__stop_threads()

    def kill(self):
        assert self.__process != None
        self.__process.kill()
        self.__stop_threads()

    def terminate(self):
        assert self.__process != None
        self.__process.terminate()
        self.__stop_threads()
