#!/usr/bin/python -u
# -* encoding: utf-8 *-

import gopythongo.main
import gopythongo.builders
import gopythongo.versioners
import gopythongo.stores
import gopythongo.assemblers
import gopythongo.packers
import atexit
import signal
import sys
import os

from configargparse import ArgParser as ArgumentParser
from gopythongo.utils import print_error, print_warning, print_info, init_color

tempfiles = []


def get_parser():
    parser = ArgumentParser(description="Build a Python virtualenv deployment artifact and collect "
                                        "a Django project's static content if needed. The created "
                                        "virtualenv is ready to be deployed to a server. "
                                        "This tool is designed to be used with pbuilder or docker so it can build a "
                                        "virtual environment in the path where it will be deployed. "
                                        "Parameters that start with '--' (eg. --mode) can "
                                        "also be set in a config file (e.g. .gopythongo) by using .ini or .yaml-style "
                                        "syntax (e.g. mode=value). If a parameter is specified in more than one place, "
                                        "then command-line values override config file values which override defaults. "
                                        "More information at http://gopythongo.com/.",
                            prog="gopythongo.main",
                            args_for_setting_config_path=["-c", "--config"],
                            config_arg_help_message="Use this path instead of the default (.gopythongo)",
                            default_config_files=[".gopythongo"])

    gr_plan = parser.add_argument_group("Execution plan")
    gr_plan.add_argument("--ecosystem", dest="ecosystem", choices=["python"], default="python",
                         help="Choose the ecosystem to build from. (Default and only option right now: Python)")
    gr_plan.add_argument("--builder", dest="builder", choices=["docker", "pbuilder"], default=None, required=True,
                         help="Select the builder used to build the project")
    gr_plan.add_argument("--assembler", dest="assembler",
                         choices=["django", "pip"], action="append",
                         help="Select one or more assemblers to build the project inside the builder, i.e. install, "
                              "compile, pull all necessary source code and libraries.")
    gr_plan.add_argument("--packer", choices=["fpm", "targz"], default=None, required=True,
                         help="Select the packer used to pack up the built project")
    gr_plan.add_argument("--store", choices=["docker", "aptly", "none"], default=None, required=True,
                         help="Select the store used to store the packed up project")
    gr_plan.add_argument("--gopythongo-path", dest="gopythongo_path", default=None,
                         help="Path to a virtual environment that contains GoPythonGo or a PEX GoPythonGo executable. "
                              "This will be mounted into the build environment.")
    gr_plan.add_argument("--inner", dest="is_inner", action="store_true", default=False,
                         help="This parameter signals to GoPythonGo that it is running inside the build environment, "
                              "you will likely never have to use this parameter yourself. It is used by GoPythonGo "
                              "internally.")

    gr_out = parser.add_argument_group("Output options")
    gr_out.add_argument("-v", "--verbose", dest="verbose", default=False, action="store_true",
                        help="more output")
    gr_out.add_argument("-V", "--version", action="version", version=gopythongo.__version__)
    gr_out.add_argument("--no-color", dest="no_color", action="store_true", default=False,
                        help="Do not use ANSI color sequences in output")

    for m in [gopythongo.builders, gopythongo.versioners, gopythongo.assemblers, gopythongo.packers, gopythongo.stores]:
        m.add_args(parser)

    return parser


def validate_args(args):
    if not args.builder:
        print_error("You must select a builder using --builder.")
        sys.exit(1)
    if not args.packer:
        print_error("You must select a packer using --packer.")
        sys.exit(1)
    if not args.store:
        print_error("You must select a store using --store.")
        sys.exit(1)

    for m in [gopythongo.builders, gopythongo.versioners, gopythongo.assemblers, gopythongo.packers, gopythongo.stores]:
        m.validate_args(args)


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


def _sigint_handler(signal, frame):
    print_warning("CTRL+BREAK. Exiting.")
    sys.exit(1)


def _cleanup_tempfiles():
    if tempfiles:
        print_info("Cleaning up temporary files...")
        for f in tempfiles:
            if os.path.exists(f):
                os.unlink(f)


def route():
    atexit.register(_cleanup_tempfiles)
    signal.signal(signal.SIGINT, _sigint_handler)

    if len(sys.argv) > 1:
        args = get_parser().parse_args()
        init_color(args.no_color)
        validate_args(args)

        if not args.is_inner:
            # STEP 1: Start the build, which will execute gopythongo.main --inner for step 2
            gopythongo.versioners.version(args)
            gopythongo.builders.build(args)

            # STEP 3: After the 2nd gopythongo process is finished, we end up here
            gopythongo.stores.store(args)
        else:
            # STEP 2: ... which will land here and execute inside the build environment
            gopythongo.versioners.version(args)
            gopythongo.assemblers.assemble(args)
            gopythongo.packers.pack(args)

    else:
        print_help()


if __name__ == "__main__":
    route()
