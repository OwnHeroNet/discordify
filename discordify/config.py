import getopt
import json
import sys
from distutils.util import strtobool
from functools import partial
from getpass import getuser
# required to get the HOME folder
from pathlib import Path
from socket import gethostname

from discordify.command import Command
from discordify.utils import compute_gravatar_url

TOOL_NAME = 'discordify'
GLOBAL_CONFIG = '/etc/{}.conf'.format(TOOL_NAME)
LOCAL_CONFIG = '{home}/.{tool}.conf'.format(home=Path.home(), tool=TOOL_NAME)


class Option:

    def __init__(self, long_opt, required=False, takes_arg=False, **kwargs):
        # TODO add validation
        self.long_opt = long_opt
        self.short_opt = kwargs.get('short_opt')

        self.takes_arg = takes_arg
        self.required = required

        self.default = kwargs.get('default')
        self.description = kwargs.get('description')
        self.example = kwargs.get('example')

        self.__parse = kwargs.get('parse')

    def __str__(self):
        string = '--' + self.long_opt
        if self.takes_arg:
            string += ' {} {}\n'.format(self.long_opt.upper(), '(Required)' if self.required else '')
        else:
            string += '\n'

        if self.short_opt:
            string += '-' + self.short_opt
            if self.takes_arg:
                string += ' {}\n'.format(self.long_opt.upper())
            else:
                string += '\n'

        if self.description:
            string += self.description
            if self.default:
                string += '\t(Default: ' + self.default + ')\n'
            else:
                string += '\n'

        if self.example:
            string += 'Example: \n\t' + self.example + '\n'

        return string

    def process(self, dictionary):
        if self.short_opt and '-' + self.short_opt in dictionary:
            if self.takes_arg:
                value = dictionary['-' + self.short_opt]
            else:
                value = True
        elif '--' + self.long_opt in dictionary:
            if self.takes_arg:
                value = dictionary['--' + self.long_opt]
            else:
                value = True
        else:
            assert False

        return self.parse(value)

    def parse(self, value):
        if self.__parse:
            return self.__parse(value)

        return value

    def contained(self, dictionary):
        return self.short_opt and '-' + self.short_opt in dictionary or '--'+self.long_opt in dictionary


class Arguments:

    class HelpRequest(Exception):

        def __init__(self):
            super().__init__('User requested help.')

    def __init__(self):
        self.options = {
            'help': Option(
                long_opt='help',
                short_opt='h',
                description='Prints this help and exits.',
                takes_arg=False,
                required=False),
            'webhook': Option(
                long_opt='webhook',
                short_opt='w',
                description='Defines the webhook\'s endpoint in Slack/Discord.',
                takes_arg=True,
                required=True),
            'title': Option(
                long_opt='title',
                description='Defines the title of the embed.',
                default='Discordify Notification',
                takes_arg=True,
                required=False),
            'description': Option(
                long_opt='description',
                description='Defines the description of the embed.',
                takes_arg=True,
                required=False),
            'image': Option(
                long_opt='image',
                description='Adds an image to the embed.',
                takes_arg=True,
                required=False),
            'title_url': Option(
                long_opt='title_url',
                description='Defines the url of the title of the embed.',
                takes_arg=True,
                required=False),
            'color': Option(
                long_opt='color',
                short_opt='c',
                description='Defines the color of the embed.',
                default="0x2176C7",
                takes_arg=True,
                required=True,
                parse=lambda s: int(s, 0)),
            'user_name': Option(
                long_opt='user_name',
                description='Defines the name of the user in the embed.',
                default='Discordify User',
                takes_arg=True,
                required=True
            ),
            'user_email': Option(
                long_opt='user_email',
                description='Defines the email of the user in the embed.',
                default='{user}@{host}'.format(user=getuser(), host=gethostname()),
                takes_arg=True,
                required=True
            ),
            'user_icon': Option(
                long_opt='user_icon',
                description='Defines the icon of the user in the embed.',
                takes_arg=True,
                required=False
            ),
            'user_url': Option(
                long_opt='user_url',
                description='Defines the url of the user in the embed.',
                default='https://github.com/OwnHeroNet/discordify',
                takes_arg=True,
                required=False
            ),
            'footer_icon': Option(
                long_opt='footer_icon',
                description='Defines the footer icon of the embed.',
                default='https://raw.githubusercontent.com/OwnHeroNet/discordify/master/logo/Icon.png',
                takes_arg=True,
                required=False
            ),
            'thumbnail': Option(
                long_opt='thumbnail',
                description='Defines the thumbnail icon of the embed.',
                takes_arg=True,
                required=False
            ),
            'periodic': Option(
                long_opt='periodic',
                short_opt='p',
                description='Defines a periodic interval (in seconds) on when to report.',
                takes_arg=True,
                required=False,
                parse=lambda s: int(s, 0)
            ),
            'icon_failure': Option(
                long_opt='icon_failure',
                description='Defines the icon in case the process failed.',
                default='https://raw.githubusercontent.com/OwnHeroNet/discordify/master/logo/Failure.png',
                takes_arg=True,
                required=False
            ),
            'icon_success': Option(
                long_opt='icon_success',
                description='Defines the icon in case the process succeeded.',
                default='https://raw.githubusercontent.com/OwnHeroNet/discordify/master/logo/Success.png',
                takes_arg=True,
                required=False
            ),
            'icon_warning': Option(
                long_opt='icon_warning',
                description='Defines the icon in case a warning was raised.',
                default='https://raw.githubusercontent.com/OwnHeroNet/discordify/master/logo/Warning.png',
                takes_arg=True,
                required=False
            ),
            'icon_period': Option(
                long_opt='icon_period',
                description='Defines the icon for periodic updates.',
                default='https://raw.githubusercontent.com/OwnHeroNet/discordify/master/logo/Period.png',
                takes_arg=True,
                required=False
            ),
            'icon_timeout': Option(
                long_opt='icon_timeout',
                description='Defines the icon for a timeout.',
                default='https://raw.githubusercontent.com/OwnHeroNet/discordify/master/logo/Timeout.png',
                takes_arg=True,
                required=False
            ),
            'timeout': Option(
                long_opt='timeout',
                short_opt='t',
                description='Configure the timeout after which the process is killed.',
                takes_arg=True,
                required=False,
                parse=lambda s: int(s, 0)
            ),
            'footer': Option(
                long_opt='footer',
                description='Defines the footnote of the embed.',
                default='via {}@{}'.format(getuser(), gethostname()),
                takes_arg=True,
                required=False
            ),
            'system_stats': Option(
                long_opt='system_stats',
                description='Enable stats about the system.',
                default='False',
                takes_arg=False,
                required=False
            ),
            'simple': Option(
                long_opt='simple',
                short_opt='s',
                description='Switch to simple mode sending a message rather than an embed.',
                takes_arg=False,
                required=False
            ),
            'buffer_size': Option(
                long_opt='buffer_size',
                description='Defines the size (number of lines) of the stdin/stdout/stderr buffers.',
                default='5',
                takes_arg=True,
                required=False,
                parse=lambda s: int(s, 0)
            )}

        self.extend_config()

    def __str__(self):
        return '\n'.join(map(lambda v: str(v[1]), sorted(self.options.items())))

    def parse(self):
        short_with_arg = ''.join(map(lambda y: y.short_opt + ':' if y.short_opt else '', filter(lambda x: x.takes_arg, self.options.values())))
        short_no_arg = ''.join(map(lambda y: y.short_opt if y.short_opt else '', filter(lambda x: not x.takes_arg, self.options.values())))
        long_opts = list(map(lambda x: x.long_opt if not x.takes_arg else x.long_opt+'=', self.options.values()))
        opts, args = getopt.getopt(sys.argv[1:], short_with_arg + short_no_arg, long_opts)

        dopts = dict(opts)
        if self.options['help'].contained(dopts):
            self.usage()
            raise Arguments.HelpRequest()

        config = Config()

        missing_options = []
        for _, option in self.options.items():
            if option.contained(dopts):
                config.config[option.long_opt] = option.process(dopts)
            elif option.long_opt in config.config:
                config.config[option.long_opt] = option.parse(str(config.config[option.long_opt]))
                pass
            elif option.default:
                dopts['--'+option.long_opt] = option.default
                config.config[option.long_opt] = option.process(dopts)
            elif option.required:
                missing_options.append(option.long_opt)

        if len(missing_options) > 0:
            print(config)
            raise getopt.GetoptError('Missing required options "{}".\n'.format(','.join(missing_options)))

        if getattr(config, "user_email") and not getattr(config, 'user_icon'):
            config.config['user_icon'] = compute_gravatar_url(getattr(config, "user_email"))

        return Command(config, args)

    def extend_config(self):
        for name in self.options:
            setattr(Config, name, property(lambda x, name=name: x.config[name] if name in x.config else None))

    def usage(self):
        print('''DISCORDIFY
==========

Discordify is a wrapper to execute UNIX shell commands and
notify a channel in either Slack or Discord about the results.

Configuration is done via /etc/dicordify.conf, ~/.discordify.conf
and the command line options (in that order).

''')
        print('USAGE: python -m discordify [OPTIONS] commands')
        print()
        print(self)


class Config:

    class InvalidConfiguration(Exception):

        def __init__(self, path, error):
            super().__init__("Invalid config at {}: {}".format(path, error))

    def __init__(self):
        self.config = {}
        self.load()

    def load(self):
        for config in [GLOBAL_CONFIG, LOCAL_CONFIG]:
            try:
                with open(config, 'r') as f:
                    try:
                        self.config.update(json.load(f))
                    except json.JSONDecodeError as err:
                        raise Config.InvalidConfiguration(config, err)

            except Exception:
                pass

    def __repr__(self):
        return json.dumps(self.config, sort_keys=True, indent=4)
