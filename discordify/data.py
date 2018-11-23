import datetime
import time
from getpass import getuser
from os import getpgid
from socket import gethostname
from discordify.mode import Mode


class Data:
    '''Holds the data to be emitted as a payload via the webhook.'''

    def __init__(self, arguments, pid: int, start_time, end_time, mode: Mode, stdin_lines, stdout_lines, stderr_lines, stdin_buffer, stdout_buffer, stderr_buffer, returncode):
        self.__command = arguments[0] if arguments and len(arguments) > 0 else None
        self.__arguments = arguments[1:] if arguments and len(arguments) > 1 else None
        self.__pid = pid
        self.__start_time = start_time
        self.__end_time = end_time
        self.__mode = mode
        self.__stdin_lines = stdin_lines
        self.__stdout_lines = stdout_lines
        self.__stderr_lines = stderr_lines
        self.__stdin_buffer = stdin_buffer
        self.__stdout_buffer = stdout_buffer
        self.__stderr_buffer = stderr_buffer
        self.__returncode = returncode
        self.__username = getuser()
        self.__hostname = gethostname()

    @property
    def argument(self):
        return self.__arguments

    @property
    def mode(self):
        return self.__mode

    @property
    def stdin_lines(self):
        return self.__stdin_lines

    @property
    def stdout_lines(self):
        return self.__stdout_lines

    @property
    def stderr_lines(self):
        return self.__stderr_lines

    @property
    def stdin_buffer(self):
        return self.__stdin_buffer

    @property
    def stdout_buffer(self):
        return self.__stdout_buffer

    @property
    def stderr_buffer(self):
        return self.__stderr_buffer

    @property
    def returncode(self):
        return self.__returncode if self.__returncode is not None else '<unavailable>'

    @property
    def runtime(self):
        return str(datetime.timedelta(seconds=self.__end_time - self.__start_time))

    @property
    def start_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.__start_time))

    @property
    def end_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.__end_time))

    @property
    def success(self):
        return self.__returncode == 0

    @property
    def pid(self):
        return self.__pid if self.__pid else getpgid(0)

    @property
    def timestamp(self):
        return str(datetime.datetime.utcfromtimestamp(time.time()))

    @property
    def command(self):
        if self.__command:
            return self.__command
        else:
            assert Mode.SINK == self.__mode
            return '<discordify SINK>'

    @property
    def hostname(self):
        return self.__hostname

    @property
    def username(self):
        return self.__username
