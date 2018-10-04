import getopt
import json
import sys
from getpass import getuser
from hashlib import md5
# required to get the HOME folder
from pathlib import Path
from socket import gethostname
from discordify.command import Command

TOOL_NAME = 'discordify'
GLOBAL_CONFIG = '/etc/{}.conf'.format(TOOL_NAME)
LOCAL_CONFIG = '{home}/.{tool}.conf'.format(home=Path.home(), tool=TOOL_NAME)


class Option:

    def __init__(self, long_opt, required=False, takes_arg=False, **kwargs):
        self.long_opt = long_opt
        self.short_opt = kwargs.get('short_opt')

        self.takes_arg = takes_arg
        self.required = required

        self.default = kwargs.get('default')
        self.description = kwargs.get('description')
        self.example = kwargs.get('example')

        self.parse = kwargs.get('parse')

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
            value = dictionary['-' + self.short_opt]
        elif '--' + self.long_opt in dictionary:
            value = dictionary['--' + self.long_opt]
        else:
            assert False

        if self.parse:
            return self.parse(value)
        return value

    def contained(self, dictionary):
        return self.short_opt and '-' + self.short_opt in dictionary or '--'+self.long_opt in dictionary


class Arguments:

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
                description='Defines the webhook\'s endpoint in Slack, Discord or Team',
                takes_arg=True,
                required=True),
            'title': Option(
                long_opt='title',
                short_opt='t',
                description='Defines the title of the embed.',
                default='Discordify Notification',
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
            'user_url': Option(
                long_opt='user_email',
                description='Defines the url of the user in the embed.',
                default='https://github.com/OwnHeroNet/discordify',
                takes_arg=True,
                required=False
            ),
            'thumbnail': Option(
                long_opt='thumbnail',
                description='Defines the thumbnail of the embed.',
                default='https://users.own-hero.net/~methos/discordify.png',
                takes_arg=True,
                required=False
            ),
            'footer': Option(
                long_opt='footer',
                description='Defines the footnote of the embed.',
                default='via {}@{}'.format(getuser(), gethostname()),
                takes_arg=True,
                required=False
            )}

    def __str__(self):
        return '\n'.join(map(lambda x: str(x), self.options.values()))

    def parse(self):
        short_with_arg = ''.join(map(lambda y: y.short_opt if y.short_opt else '', filter(lambda x: x.takes_arg, self.options.values())))
        short_no_arg = ':'.join(map(lambda y: y.short_opt if y.short_opt else '', filter(lambda x: not x.takes_arg, self.options.values())))
        long_opts = list(map(lambda x: x.long_opt if not x.takes_arg else x.long_opt+'=', self.options.values()))
        opts, args = getopt.getopt(sys.argv[1:], short_with_arg + ':' + short_no_arg, long_opts)

        dopts = dict(opts)
        if self.options['help'].contained(dopts):
            self.usage()
            exit(0)

        config = Config()

        missing_options = []
        for _, option in self.options.items():
            if option.contained(dopts):
                config.config[option.long_opt] = option.process(dopts)
            elif option.long_opt in config.config:
                pass
            elif option.default:
                dopts['--'+option.long_opt] = option.default
                config.config[option.long_opt] = option.process(dopts)
            elif option.required:
                missing_options.append(option.long_opt)

        if len(missing_options) > 0:
            print(config)
            raise getopt.GetoptError('Missing required options "{}".\n'.format(','.join(missing_options)))

        return Command(config, args)

    def usage(self):
        print('''DISCORDIFY
==========

Discordify is a wrapper to execute UNIX shell commands and
notify a channel in either Slack or Discord about the results.

Configuration is done via /etc/dicordify.conf, ~/.discordify.conf 
and the command line options (in that order).

''')
        print('USAGE: {} [OPTIONS] commands'.format(sys.argv[0]))
        print()
        print(self)


class Config:

    def __init__(self):
        self.config = {}
        self.load()

    @staticmethod
    def compute_gravatar_url(email):
        email = email.strip().lower()
        hash = md5(email.encode("utf8")).hexdigest()
        return 'https://www.gravatar.com/avatar/{hash}?s=128'.format(hash=hash)

    def load(self):
        for config in [GLOBAL_CONFIG, LOCAL_CONFIG]:
            try:
                with open(config, 'r') as f:
                    try:
                        self.config.update(json.load(f))
                    except json.JSONDecodeError as err:
                        print("Invalid config at {}: {}".format(config, err))
                        exit(34)

            except Exception:
                pass

        if 'user_icon' not in self.config and 'user_email' in self.config:
            email = self.config['user_email']
            self.config['user_icon'] = Config.compute_gravatar_url(email)

        self.__check()

    def __check(self):
        pass

    def get_webhook(self):
        return self.config['webhook']

    def get_user_name(self):
        return self.config['user_name']

    def get_user_url(self):
        return self.config['user_url']

    def get_user_icon(self):
        return self.config['user_icon'] if 'user_icon' in self.config else None

    def get_color(self):
        return self.config['color']

    def get_title(self):
        return self.config['title']

    def get_title_url(self):
        return self.config['title_url'] if 'title_url' in self.config else None

    def get_description(self):
        return self.config['description'] if 'description' in self.config else 'empty'

    def get_image(self):
        return self.config['description'] if 'description' in self.config else None

    def get_thumbnail(self):
        return self.config['thumbnail'] if 'thumbnail' in self.config else 'https://users.own-hero.net/~methos/discordify.png'

    def get_footer(self):
        return self.config['footer'] if 'footer' in self.config else 'Empty'

    def get_footer_icon(self):
        return self.config['footer_icon'] if 'footer_icon' in self.config else None

    def get_message(self):
        return self.config['message'] if 'message' in self.config else None

    def __repr__(self):
        return json.dumps(self.config, sort_keys=True, indent=4)
