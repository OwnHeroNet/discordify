import getopt
import sys
from config import Config
from command import Command
from payload import Payload

EXIT_INVALID_ARGS = 0x01
EXIT_NO_ARGS_NO_PIPE = 0x02


def usage():
    print('USAGE: ...')


def setup(opts):
    verbose = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    return Config()


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:v", ["help", "output="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)
        usage()
        sys.exit(EXIT_INVALID_ARGS)

    config = setup(opts)
    # print(config)

    if len(args) == 0:
        if not sys.stdin.isatty():
            # only used at end of pipe.
            # wait for EOF on STDIN
            for line in sys.stdin:
                sys.stdout.write(line)
            payload = Payload(config)
            payload.done()
            exit(0)
        else:
            print('Invalid usage.')
            usage()
            exit(EXIT_NO_ARGS_NO_PIPE)

    cmd = Command(config, args)
    cmd.run()

    cmd.wait()


if __name__ == '__main__':
    main()
