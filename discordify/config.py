import json
# required to get the HOME folder
from pathlib import Path
from socket import gethostname
from getpass import getuser
from hashlib import md5

TOOL_NAME = 'discordify'
GLOBAL_CONFIG = '/etc/{}.conf'.format(TOOL_NAME)
LOCAL_CONFIG = '{home}/.{tool}.conf'.format(home=Path.home(), tool=TOOL_NAME)

DEFAULT_CONFIG = {
    # 'webhook': 'https://discordapp.com/api/webhooks/492811299869294593/MjIZLJTSqfelXbSFEbVidAJ_AipFRhSAonI_fwoj0QzgDdEUnARQkGwmhAziNgHdnwYb',
    'webhook': 'https://discordapp.com/api/webhooks/497216199852163092/qDWKLKXgbMOV3Lk4hRzliyFAk76Lt7G3R8y3tVORc0cyjqWuNtdihBigfs3bf3hZJUVP',
    'user_name': 'Discordify User',
    'user_email': '{user}@{host}'.format(user=getuser(), host=gethostname()),
    'user_url': 'https://sascha-just.com',
    'title': 'Discordify Notification',
    'thumbnail': 'https://users.own-hero.net/~methos/discordify.png',
    'footer': 'via {}'.format(gethostname()),
    'color': 0x2176C7
}


class Config:

    def __init__(self):
        self.__config = DEFAULT_CONFIG
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
                    self.__config.update(json.load(f))
            except Exception:
                pass

        # self.__config['user_url'] = 'mailto:sascha.just@own-hero.net'
        if 'user_icon' not in self.__config and 'user_email' in self.__config:
            email = self.__config['user_email']
            self.__config['user_icon'] = Config.compute_gravatar_url(email)

        self.__check()

    def __check(self):
        pass

    def get_webhook(self):
        return self.__config['webhook']

    def get_user_name(self):
        return self.__config['user_name']

    def get_user_url(self):
        return self.__config['user_url']

    def get_user_icon(self):
        return self.__config['user_icon'] if 'user_icon' in self.__config else None

    def get_color(self):
        return self.__config['color']

    def get_title(self):
        return self.__config['title']

    def get_title_url(self):
        return self.__config['title_url'] if 'title_url' in self.__config else None

    def get_description(self):
        return self.__config['description'] if 'description' in self.__config else 'empty'

    def get_image(self):
        return self.__config['description'] if 'description' in self.__config else None

    def get_thumbnail(self):
        return self.__config['thumbnail'] if 'thumbnail' in self.__config else 'https://users.own-hero.net/~methos/discordify.png'

    def get_footer(self):
        return self.__config['footer'] if 'footer' in self.__config else 'Empty'

    def get_footer_icon(self):
        return self.__config['footer_icon'] if 'footer_icon' in self.__config else None

    def get_message(self):
        return self.__config['message'] if 'message' in self.__config else None

    def __repr__(self):
        return json.dumps(self.__config, sort_keys=True, indent=4)
