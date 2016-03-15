#!/usr/bin/python -u
# -* coding: utf-8 *-

import gopythongo.main
import gopythongo.assemble
import gopythongo.build
import sys


commands = {
    "assemble": gopythongo.assemble,
    "build": gopythongo.build,
    "help": sys.modules[__name__],  # invoke this module's .main()
}


def print_help():
    print("Usage: python -m gopythongo.main build|assemble|help")
    print("")
    print("    build          - build a package or container using gopythongo")
    print("    assemble       - assemble a build inside a container or chroot (usually invoked by 'build')")
    print("    help [command] - print this message or help for a specific command")
    print("")
    print("Find more information at http://gopythongo.com/")


def route():
    if len(sys.argv) > 1 and sys.argv[1] in commands:
        commands[sys.argv[1]].main()
    else:
        if len(sys.argv) > 1:
            print("*** Unknown command: %s" % sys.argv[1])
        print_help()


def main():
    # sys.argv[1] == "help"
    if len(sys.argv) > 2 and sys.argv[2] in commands:
        commands[sys.argv[2]].get_parser().print_help()
    else:
        print_help()


if __name__ == "__main__":
    route()
