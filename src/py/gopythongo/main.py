#!/usr/bin/python -u
# -* coding: utf-8 *-

import gopythongo.main
import gopythongo.assemble
import gopythongo.pack
import gopythongo.build
import sys


commands = {
    "assemble": gopythongo.assemble,
    "build": gopythongo.build,
    "pack": gopythongo.pack,
    "help": sys.modules[__name__],  # invoke this module's .main()
}


def add_common_parameters_to_parser(parser):
    gr_mode = parser.add_argument_group("General settings")
    gr_mode.add_argument("--mode", dest="mode", choices=["deb", "tar", "docker"], default="deb",
                         help="Build a .tar.gz old-style bundle, a Docker container or a .deb package")
    gr_mode.add_argument("-o", "--output", dest="outfile", required=True,
                         help="output filename for the .tar.gz bundle or Debian package")
    gr_mode.add_argument("--apt-get", dest="build_deps", action="append",
                         help="Packages to install using apt-get prior to creating the virtualenv (e.g. driver libs "
                              "for databases so that Python C extensions compile correctly.")

    return parser



def print_help():
    print("Usage: python -m gopythongo.main build|assemble|help")
    print("")
    print("    build          - build a package or container using gopythongo")
    print("    assemble       - assemble a build inside a container or chroot (usually")
    print("                     invoked by 'build')")
    print("    pack           - create a Docker container, deb package or .tar.gz archive")
    print("                     (usually invoked by 'build')")
    print("    help [command] - print this message or help for a specific command")
    print("")
    print("While the command-line interface provides a useful reference and can be")
    print("used for testing and development, you really want to put all build")
    print("instructions into a .gopythongo rc file inside your project.")
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
