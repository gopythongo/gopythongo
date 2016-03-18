#!/usr/bin/python -u
# -* encoding: utf-8 *-

import gopythongo.main
import gopythongo.build
import gopythongo.prepare
import gopythongo.assemble
import gopythongo.pack
import atexit
import sys
import os


commands = {
    "build": gopythongo.build,
    "prepare": gopythongo.prepare,
    "assemble": gopythongo.assemble,
    "pack": gopythongo.pack,
    "help": sys.modules[__name__],  # invoke this module's .main()
}

tempfiles = []


def add_common_parameters_to_parser(parser):
    gr_mode = parser.add_argument_group("General settings")
    gr_mode.add_argument("--mode", dest="mode", choices=["deb", "docker"], default="deb",
                         help="Build a Docker container or a .deb package")
    gr_mode.add_argument("-o", "--output", dest="outfile", required=True,
                         help="output filename for the .tar.gz bundle or Debian package")
    gr_mode.add_argument("--apt-get", dest="build_deps", action="append",
                         help="Packages to install using apt-get prior to creating the virtualenv (e.g. driver libs "
                              "for databases so that Python C extensions compile correctly.")

    gr_out = parser.add_argument_group('Output options')
    gr_out.add_argument("-v", "--verbose", dest="verbose", default=False, action="store_true",
                        help="more output")

    return parser


def print_help():
    print("Usage: python -m gopythongo.main build|prepare|assemble|pack|help")
    print("")
    print("    build          - build a package or container using gopythongo. This")
    print("                     will run prepare on the build machine and then run")
    print("                     assemble->pack inside the container or chroot.")
    print("    prepare        - Create a build container or chroot, install dependencies and")
    print("                     mount host paths.")
    print("    assemble       - assemble a build inside a container or chroot (usually")
    print("                     invoked by 'build').")
    print("    pack           - create a Docker container, deb package or .tar.gz archive")
    print("                     (usually invoked by 'build').")
    print("    help [command] - print this message or help for a specific command.")
    print("")
    print("While the command-line interface provides a useful reference and can be")
    print("used for testing and development, you really want to put all build")
    print("instructions into a .gopythongo rc file inside your project.")
    print("")
    print("Generally you will then only call 'build' which will run assemble and pack as")
    print("needed.")
    print("")
    print("You can find more information at http://gopythongo.com/")


def _cleanup_tmpfiles():
    print("Cleaning up temporary files...")
    for f in tempfiles:
        if os.path.exists(f):
            os.unlink(f)


def route():
    atexit.register(_cleanup_tmpfiles)
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
