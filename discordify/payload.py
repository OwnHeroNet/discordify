import datetime
import json
import os
import sys
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from discordify.mode import Mode
import requests

TEST_MODE = os.environ.get('DISCORDIFY_TESTING')


class Payload(ABC):

    def __init__(self, config, data):
        self.__config = config
        self.__data = data
        self.__payload = {}

    @staticmethod
    def create(config, data):
        if config.simple:
            return Message(config, data)
        else:
            return Embed(config, data)

    @abstractmethod
    def emit_final(self):
        pass

    @abstractmethod
    def emit_timeout(self):
        pass

    @abstractmethod
    def emit_period(self):
        pass

    @abstractmethod
    def emit_signal(self):
        pass

    @abstractmethod
    def emit_interrupt(self):
        pass

    @property
    def config(self):
        return self.__config

    @property
    def data(self):
        return self.__data

    @property
    def payload(self):
        return self.__payload

    @property
    def json(self):
        '''
        Formats the data into a payload.
        '''
        return json.dumps(self.payload, indent=4)

    def post(self):
        """
        Send the JSON formated object to the specified `self.url`.
        """

        headers = {'Content-Type': 'application/json'}

        if TEST_MODE:
            print(self.json)
            return

        result = requests.post(self.__config.webhook, data=self.json, headers=headers)

        if result.status_code >= 400:
            print(self.json)
            print("Post Failed, Error {}".format(result.status_code), file=sys.stderr)


class Message(Payload):

    def __init__(self, config, data):
        super().__init__(config, data)

    def emit_timeout(self):
        self.payload["content"] = '{emoticon} Your `{command}` command on `{hostname}` started by `{username}` just timed out after {runtime}.'.format(
            emoticon=':clock4:',
            command=self.data.command,
            hostname=self.data.hostname,
            username=self.data.username,
            runtime=self.data.runtime
        )
        self.post()

    def emit_signal(self):
        self.payload["content"] = '{emoticon} Forced update on your `{command}` command on `{hostname}` started by `{username}` is running for {runtime}.'.format(
            emoticon=':pushpin:',
            command=self.data.command,
            hostname=self.data.hostname,
            username=self.data.username,
            runtime=self.data.runtime
        )
        self.post()

    def emit_period(self):
        self.payload["content"] = '{emoticon} Periodic update on your `{command}` command on `{hostname}` started by `{username}` is running for {runtime}.'.format(
            emoticon=':arrows_counterclockwise:',
            command=self.data.command,
            hostname=self.data.hostname,
            username=self.data.username,
            runtime=self.data.runtime
        )
        self.post()

    def emit_interrupt(self):
        self.payload["content"] = '{emoticon} Your `{command}` command on `{hostname}` started by `{username}` just was interrupted after {runtime}.'.format(
            emoticon=':octagonal_sign:',
            command=self.data.command,
            hostname=self.data.hostname,
            username=self.data.username,
            runtime=self.data.runtime
        )
        self.post()

    def emit_final(self):
        self.payload["content"] = '{emoticon} Your `{command}` command on `{hostname}` started by `{username}` just finished after {runtime}.'.format(
            emoticon=':white_check_mark:' if self.data.success else ':x:',
            command=self.data.command,
            hostname=self.data.hostname,
            username=self.data.username,
            runtime=self.data.runtime
        )
        self.post()


class Embed(Payload):

    def __init__(self, config, data):
        super().__init__(config, data)

    def __prepare_defaults(self):
        embed = defaultdict(dict)

        embed["color"] = self.config.color

        embed["author"]["name"] = self.config.user_name
        embed["author"]["icon_url"] = self.config.user_icon
        embed["author"]["url"] = self.config.user_url

        if (self.config.title_url):
            embed["url"] = self.config.title_url

        if self.config.image:
            embed["image"]['url'] = self.config.image

        if self.config.footer:
            embed["footer"]['text'] = self.config.footer
        if self.config.footer_icon:
            embed['footer']['icon_url'] = self.config.footer_icon

        embed["timestamp"] = self.data.timestamp

        return embed

    def emit_period(self):
        embed = self.__prepare_defaults()

        # set the icon
        embed["thumbnail"]['url'] = self.config.icon_period

        embed["title"] = 'Periodic update on `[' + self.data.pid + '] ' + self.data.command + '`'

        # >>> description
        desc = ''
        if len(self.data.stdin_buffer) > 0:
            desc += '**STDIN buffer:**\n```\n' + self.data.stdin_buffer + '\n```'
        if len(self.data.stdout_buffer) > 0:
            desc += '\n**STDOUT buffer:**\n```\n' + self.data.stdout_buffer + '\n```'
        if len(self.data.stderr_buffer) > 0:
            desc += '\n**STDERR buffer:**\n```\n' + self.data.stderr_buffer + '\n```'
        embed["description"] = desc
        # <<< description

        embed["fields"] = []

        def append(name, value):
            embed["fields"].append({"name": name, "value": value, "inline": True})

        append('Run time', self.data.runtime)
        append('Start time', self.data.start_time)

        append('STDIN',  '{} lines'.format(self.data.stdin_lines))
        append('STDOUT', '{} lines'.format(self.data.stdout_lines))
        append('STDERR', '{} lines'.format(self.data.stderr_lines))

        self.payload["embeds"] = []
        self.payload["embeds"].append(dict(embed))

        self.post()

    def emit_signal(self):
        embed = self.__prepare_defaults()

        # set the icon
        embed["thumbnail"]['url'] = self.config.icon_warning

        embed["title"] = 'Forced update on `[' + self.data.pid + '] ' + self.data.command + '`'

        # >>> description
        desc = ''
        if len(self.data.stdin_buffer) > 0:
            desc += '**STDIN buffer:**\n```\n' + self.data.stdin_buffer + '\n```'
        if len(self.data.stdout_buffer) > 0:
            desc += '\n**STDOUT buffer:**\n```\n' + self.data.stdout_buffer + '\n```'
        if len(self.data.stderr_buffer) > 0:
            desc += '\n**STDERR buffer:**\n```\n' + self.data.stderr_buffer + '\n```'
        embed["description"] = desc
        # <<< description

        embed["fields"] = []

        def append(name, value):
            embed["fields"].append({"name": name, "value": value, "inline": True})

        append('Run time', self.data.runtime)
        append('Start time', self.data.start_time)

        append('STDIN',  '{} lines'.format(self.data.stdin_lines))
        append('STDOUT', '{} lines'.format(self.data.stdout_lines))
        append('STDERR', '{} lines'.format(self.data.stderr_lines))

        self.payload["embeds"] = []
        self.payload["embeds"].append(dict(embed))

        self.post()

    def emit_final(self):
        embed = self.__prepare_defaults()

        # set the icon
        embed["thumbnail"]['url'] = self.config.icon_success if self.data.success else self.config.icon_failure

        embed["title"] = '**CMD:** `' + self.data.command + '`'

        # >>> description
        desc = ''

        if self.data.mode != Mode.SINK:
            desc += '**Arguments:**\n```\n'
            for arg in self.data.arguments:
                desc += '[' + arg + ']\n'
            desc += '```\n'

        if len(self.data.stdin_buffer) > 0:
            desc += '**STDIN buffer:**\n```\n' + self.data.stdin_buffer + '\n```'
        if len(self.data.stdout_buffer) > 0:
            desc += '\n**STDOUT buffer:**\n```\n' + self.data.stdout_buffer + '\n```'
        if len(self.data.stderr_buffer) > 0:
            desc += '\n**STDERR buffer:**\n```\n' + self.data.stderr_buffer + '\n```'
        embed["description"] = desc
        # <<< description

        embed["fields"] = []

        def append(name, value):
            embed["fields"].append({"name": name, "value": value, "inline": True})

        append('Return Code', self.data.returncode)

        append('Run time', self.data.runtime)
        append('Start time', self.data.start_time)
        append('End time', self.data.end_time)

        append('STDIN',  '{} lines'.format(self.data.stdin_lines))
        append('STDOUT', '{} lines'.format(self.data.stdout_lines))
        append('STDERR', '{} lines'.format(self.data.stderr_lines))

        self.payload["embeds"] = []
        self.payload["embeds"].append(dict(embed))

        self.post()

    def emit_interrupt(self):
        embed = self.__prepare_defaults()

        # set the icon
        embed["thumbnail"]['url'] = self.config.icon_timeout

        embed["title"] = '**Interrupted CMD:** `' + self.data.command + '`'

        # >>> description
        desc = ''

        if self.data.mode != Mode.SINK:
            desc += '**Arguments:**\n```\n'
            for arg in self.data.arguments:
                desc += '[' + arg + ']\n'
            desc += '```\n'

        if len(self.data.stdin_buffer) > 0:
            desc += '**STDIN buffer:**\n```\n' + self.data.stdin_buffer + '\n```'
        if len(self.data.stdout_buffer) > 0:
            desc += '\n**STDOUT buffer:**\n```\n' + self.data.stdout_buffer + '\n```'
        if len(self.data.stderr_buffer) > 0:
            desc += '\n**STDERR buffer:**\n```\n' + self.data.stderr_buffer + '\n```'
        embed["description"] = desc
        # <<< description

        embed["fields"] = []

        def append(name, value):
            embed["fields"].append({"name": name, "value": value, "inline": True})

        append('Return Code', self.data.returncode)

        append('Run time', self.data.runtime)
        append('Start time', self.data.start_time)
        append('End time', self.data.end_time)

        append('STDIN',  '{} lines'.format(self.data.stdin_lines))
        append('STDOUT', '{} lines'.format(self.data.stdout_lines))
        append('STDERR', '{} lines'.format(self.data.stderr_lines))

        self.payload["embeds"] = []
        self.payload["embeds"].append(dict(embed))

        self.post()

    def emit_timeout(self):
        embed = self.__prepare_defaults()

        # set the icon
        embed["thumbnail"]['url'] = self.config.icon_timeout

        embed["title"] = '**Timed out CMD:** `' + self.data.command + '`'

        # >>> description
        desc = ''

        if self.data.mode != Mode.SINK:
            desc += '**Arguments:**\n```\n'
            for arg in self.data.arguments:
                desc += '[' + arg + ']\n'
            desc += '```\n'

        if len(self.data.stdin_buffer) > 0:
            desc += '**STDIN buffer:**\n```\n' + self.data.stdin_buffer + '\n```'
        if len(self.data.stdout_buffer) > 0:
            desc += '\n**STDOUT buffer:**\n```\n' + self.data.stdout_buffer + '\n```'
        if len(self.data.stderr_buffer) > 0:
            desc += '\n**STDERR buffer:**\n```\n' + self.data.stderr_buffer + '\n```'
        embed["description"] = desc
        # <<< description

        embed["fields"] = []

        def append(name, value):
            embed["fields"].append({"name": name, "value": value, "inline": True})

        append('Return Code', self.data.returncode)

        append('Run time', self.data.runtime)
        append('Start time', self.data.start_time)
        append('End time', self.data.end_time)

        append('STDIN',  '{} lines'.format(self.data.stdin_lines))
        append('STDOUT', '{} lines'.format(self.data.stdout_lines))
        append('STDERR', '{} lines'.format(self.data.stderr_lines))

        self.payload["embeds"] = []
        self.payload["embeds"].append(dict(embed))

        self.post()
