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

    gr_plan = parser.add_argument_group("Execution plan")
    gr_plan.add_argument("--ecosystem", dest="ecosystem", choices=["python"], default="python",
                         help="Choose the ecosystem to build from. (Default and only option right now: Python)")
    gr_plan.add_argument("--builder", dest="builder", choices=["docker", "pbuilder"],
                         help="Select the builder used to build the project")
    gr_plan.add_argument("--versioner", dest="versioner", choices=["aptly", "pymodule", "static"],
                         help="Select the versioner used to select the version string for the build")
    gr_plan.add_argument("--assembler", dest="assembler",
                         choices=["django", "pip"], action="append",
                         help="Select one or more assemblers to build the project inside the builder, i.e. install, "
                              "compile, pull all necessary source code and libraries.")
    gr_plan.add_argument("--packer", choices=["fpm", "targz"],
                         help="Select the packer used to pack up the built project")
    gr_plan.add_argument("--store", choices=["docker", "aptly"],
                         help="Select the store used to store the packed up project")

    gr_out = parser.add_argument_group("Output options")
    gr_out.add_argument("-v", "--verbose", dest="verbose", default=False, action="store_true",
                        help="more output")

    for m in [gopythongo.builders, gopythongo.assemblers, gopythongo.packers, gopythongo.stores]:
        m.add_args(parser)

    return parser


def print_help():
    print("Usage: python -m gopythongo.main [--help] -c [configfile]")
    print("")
    print("While the command-line interface provides a useful reference and can be")
    print("used for testing and development, you really want to put all build")
    print("instructions into a .gopythongo rc file inside your project.")
    print("")
    print("    --help        Run \"python -m gopythongo.main --help\" to get more help.")
    print("")
    print("You can also find more information at http://gopythongo.com/.")


def _cleanup_tempfiles():
    if tempfiles:
        print("Cleaning up temporary files...")
        for f in tempfiles:
            if os.path.exists(f):
                os.unlink(f)


def route():
    atexit.register(_cleanup_tempfiles)
    if len(sys.argv) > 1:
        get_parser().parse_args()
    else:
        print_help()


if __name__ == "__main__":
    route()
