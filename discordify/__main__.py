import getopt
import sys

import discordify.exit_codes as codes
from discordify.command import Command
from discordify.config import Arguments, Config


def main():
    arguments = Arguments()

    try:
        command = arguments.parse()
        try:
            command.run()
            command.wait()
        except (KeyboardInterrupt, SystemExit):
            command.handle_interrupt()
        sys.exit(command.exit_code)
    except Arguments.HelpRequest:
        arguments.usage()
        exit(codes.EXIT_OK)
    except Config.InvalidConfiguration as err:
        print(err, file=sys.stderr)
        exit(codes.EXIT_INVALID_CONFIG)
    except getopt.GetoptError as err:
        print(err, file=sys.stderr)
        print('See --help for usage information.', file=sys.stderr)
        sys.exit(codes.EXIT_INVALID_ARGS)


if __name__ == '__main__':
    main()
