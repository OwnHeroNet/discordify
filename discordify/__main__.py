import getopt
import sys
from discordify.command import Command
from discordify.config import Arguments

EXIT_INVALID_ARGS = 0x01


def main():
    arguments = Arguments()

    try:
        command = arguments.parse()
        try:
            command.run()
            command.wait()
        except (KeyboardInterrupt, SystemExit):
            command.handle_interrupt()

        sys.exit(0)
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)
        arguments.usage()
        sys.exit(EXIT_INVALID_ARGS)


if __name__ == '__main__':
    main()
