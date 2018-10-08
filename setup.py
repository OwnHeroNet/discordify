from setuptools import setup

setup(name='discordify',
      version='0.1',
      description='Execute UNIX shell commands and send results to a slack/discord webhook.',
      url='http://github.com/OwnHeroNet/discordify',
      author='Sascha Just',
      author_email='sascha.just@own-hero.net',
      license='MIT',
      packages=['discordify'],
      install_requires=[
          'requests',
          'psutil'
      ],
      zip_safe=False)
