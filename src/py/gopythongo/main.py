#!/usr/bin/python -u
# -* encoding: utf-8 *-

import gopythongo.main
import gopythongo.builders
import gopythongo.stores
import gopythongo.assemblers
import gopythongo.packers
import atexit
import sys
import os

from configargparse import ArgParser as ArgumentParser

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


def add_parser(subparsers):
    pass


def get_parser():
    parser = ArgumentParser(description="Build a Python virtualenv deployment artifact and collect "
                                        "a Django project's static content if needed. The created "
                                        "virtualenv is ready to be deployed to a server. "
                                        "This tool is designed to be used with pbuilder so it can build a virtual "
                                        "environment in the path where it will be deployed within a chroot. "
                                        "Parameters that start with '--' (eg. --mode) can "
                                        "also be set in a config file (.gopythongo) by using .ini or .yaml-style "
                                        "syntax (eg. mode=value). If a parameter is specified in more than one place, "
                                        "then command-line values override config file values which override defaults. "
                                        "More information at http://gopythongo.com/.",
                            prog="gopythongo.main",
                            args_for_setting_config_path=["-c", "--config"],
                            config_arg_help_message="Use this path instead of the default (.gopythongo)",
                            default_config_files=[".gopythongo"])
    add_common_parameters_to_parser(parser)
    subparsers = parser.add_subparsers()
    for m in [gopythongo.builders, gopythongo.assemblers, gopythongo.packers, gopythongo.stores]:
        m.add_parser(subparsers)

    return parser


def print_help():
    print("Usage: python -m gopythongo.main -c [configfile]")
    print("")
    print("While the command-line interface provides a useful reference and can be")
    print("used for testing and development, you really want to put all build")
    print("instructions into a .gopythongo rc file inside your project.")
    print("")
    print("You can find more information at http://gopythongo.com/.")


def _cleanup_tmpfiles():
    if tempfiles:
        print("Cleaning up temporary files...")
        for f in tempfiles:
            if os.path.exists(f):
                os.unlink(f)


def route():
    atexit.register(_cleanup_tmpfiles)
    if len(sys.argv) > 1:
        get_parser().parse_args()
    else:
        print_help()


if __name__ == "__main__":
    route()
