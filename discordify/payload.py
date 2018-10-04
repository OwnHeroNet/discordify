import datetime
import json
import sys
import time
from collections import defaultdict

import requests


class Payload:

    def __init__(self, config):
        self.__webhook = config.get_webhook()
        self.msg = config.get_message()
        self.color = config.get_color()

        self.title = config.get_title()
        self.title_url = config.get_title_url()

        self.author = config.get_user_name()
        self.author_icon = config.get_user_icon()
        self.author_url = config.get_user_url()

        self.desc = config.get_description()

        self.fields = []

        self.image = config.get_image()
        self.thumbnail = config.get_thumbnail()

        self.footer = config.get_footer()
        self.footer_icon = config.get_footer_icon()
        self.ts = None

    def prepare(self, cmd, pid, start, end, returncode, stdin_lines, stdout_lines, stderr_lines, stdin_buffer, stdout_buffer, stderr_buffer):
        self.title = '**CMD:** `{}`'.format(cmd)

        self.desc = ''
        if len(stdin_buffer) > 0:
            self.desc += '**STDIN buffer:**\n```\n' + stdin_buffer + '\n```'
        if len(stdout_buffer) > 0:
            self.desc += '\n**STDOUT buffer:**\n```\n' + stdout_buffer + '\n```'
        if len(stderr_buffer) > 0:
            self.desc += '\n**STDERR buffer:**\n```\n' + stderr_buffer + '\n```'

        runtime = datetime.timedelta(seconds=end - start)
        self.add_field('Return Code', returncode)
        self.add_field('Run time', str(runtime))

        self.add_field('Start time', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)))
        self.add_field('End time', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end)))
        self.add_field('STDIN',  '{} lines'.format(stdin_lines))
        self.add_field('STDOUT', '{} lines'.format(stdout_lines))
        self.add_field('STDERR', '{} lines'.format(stderr_lines))

        self.ts = str(datetime.datetime.utcfromtimestamp(time.time()))

        self.post()

    def add_field(self, name, value, inline=True):
        '''Adds a field to `self.fields`'''

        field = {
            'name': name,
            'value': value,
            'inline': inline
        }

        self.fields.append(field)

    def set_desc(self, desc):
        self.desc = desc

    def __set_author(self, author, icon=None, url=None):
        self.author = author
        if icon:
            self.author_icon = icon
        if url:
            self.author_url = url

    def __set_title(self, title, url=None):
        self.title = title
        if url:
            self.title_url = url

    def __set_thumbnail(self, url):
        self.thumbnail = url

    def __set_image(self, url):
        self.image = url

    def __set_footer(self, text, icon=None, timestamp=True):
        self.footer = text
        if icon:
            self.footer_icon = icon

        if not timestamp:
            return
        elif timestamp == True:
            self.ts = str(datetime.datetime.utcfromtimestamp(time.time()))
        else:
            self.ts = str(datetime.datetime.utcfromtimestamp(timestamp))

    def __del_field(self, index):
        self.fields.pop(index)

    @property
    def json(self, *arg):
        '''
        Formats the data into a payload
        '''

        data = {}

        data["embeds"] = []

        embed = defaultdict(dict)
        if self.msg:
            data["content"] = self.msg
        else:
            if self.author:
                embed["author"]["name"] = self.author
            if self.author_icon:
                embed["author"]["icon_url"] = self.author_icon
            if self.author_url:
                embed["author"]["url"] = self.author_url
            if self.color:
                embed["color"] = self.color
            if self.desc:
                embed["description"] = self.desc
            if self.title:
                embed["title"] = self.title
            if self.title_url:
                embed["url"] = self.title_url
            if self.image:
                embed["image"]['url'] = self.image
            if self.thumbnail:
                embed["thumbnail"]['url'] = self.thumbnail
            if self.footer:
                embed["footer"]['text'] = self.footer
            if self.footer_icon:
                embed['footer']['icon_url'] = self.footer_icon
            if self.ts:
                embed["timestamp"] = self.ts

            if self.fields:
                embed["fields"] = []
                for field in self.fields:
                    f = {}
                    f["name"] = field['name']
                    f["value"] = field['value']
                    f["inline"] = field['inline']
                    embed["fields"].append(f)

            data["embeds"].append(dict(embed))

        empty = all(not d for d in data["embeds"])

        if empty and 'content' not in data:
            print('You can\'t post an empty payload.', file=sys.stderr)
        if empty:
            data['embeds'] = []

        return json.dumps(data, indent=4)

    def post(self):
        """
        Send the JSON formated object to the specified `self.url`.
        """

        headers = {'Content-Type': 'application/json'}

        result = requests.post(self.__webhook, data=self.json, headers=headers)

        if result.status_code == 400:
            print(self.json)
            print("Post Failed, Error 400", file=sys.stderr)
        # else:
        #     print("Payload delivered successfuly", file=sys.stderr)
        #     print("Code : "+str(result.status_code), file=sys.stderr)


class TeamsPayload(Payload):

    def __init__(self, config):
        super().__init__(config)

    @property
    def json(self):
        '''see https://github.com/rveachkc/pymsteams'''
        pass
