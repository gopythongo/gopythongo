#!/usr/bin/python -u
# -* encoding: utf-8 *-
import argparse
import atexit
import signal
import sys
import os

from configargparse import ArgParser as ArgumentParser
from types import FrameType
from typing import List, Any, Iterable

import gopythongo

from gopythongo import initializers, builders, versioners, assemblers, packers, stores, utils
from gopythongo.utils import highlight, print_error, print_warning, print_info, init_color, ErrorMessage

tempfiles = []  # type: List[str]


class DebugConfigAction(argparse.Action):
    def __init__(self,
                 option_strings: str,
                 dest: str,
                 default: Any=None,
                 choices: Iterable[Any]=None,
                 help: str="Show all configuration keys and where they were loaded from, i.e. from the command-line, "
                           "a configuration file, or the environment") -> None:
        super().__init__(option_strings=option_strings, dest=dest, default=default,
                         nargs="?", choices=choices, help=help)

    def __call__(self, parser: ArgumentParser, namespace: argparse.Namespace,
                 values: str, option_string: str=None) -> None:
        parser.print_values()
        parser.exit(0)


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Build a Python virtualenv deployment artifact and collect "
                                        "a Django project's static content if needed. The created "
                                        "virtualenv is packaged and ready to be deployed to a server. "
                                        "This tool is designed to be used with pbuilder or docker so it can build a "
                                        "virtual environment in the path where it will be deployed. "
                                        "Parameters that start with '--' (eg. --builder) can "
                                        "also be set in a config file (e.g. .gopythongo/config) by using .ini or "
                                        ".yaml-style syntax (e.g. mode=value). If a parameter is specified in more "
                                        "than one place, then command-line values override config file values which "
                                        "override defaults. More information at http://gopythongo.com/.",
                            prog="gopythongo.main",
                            args_for_setting_config_path=["-c", "--config"],
                            config_arg_help_message="Use this path instead of the default (.gopythongo/config)",
                            default_config_files=[".gopythongo/config"])

    for subargs in [initializers.add_args, builders.add_args, versioners.add_args, assemblers.add_args,
                    packers.add_args, stores.add_args]:
        subargs(parser)

    gr_plan = parser.add_argument_group("Execution plan")
    gr_plan.add_argument("--ecosystem", dest="ecosystem", choices=["python"], default="python",
                         help="Choose the ecosystem to build from. (Default and only option right now: Python)")
    gr_plan.add_argument("--builder", dest="builder", choices=builders.builders.keys(), default=None,
                         required=True,
                         help="Select the builder used to build the project")

    # right now we _always_ run the virtualenv assembler (argparse will always *append* to the default list)
    # because gopythongo does not support non-python ecosystems.
    gr_plan.add_argument("--assembler", dest="assemblers",
                         choices=assemblers.assemblers.keys(), action="append", default=["virtualenv"],
                         help="Select one or more assemblers to build the project inside the builder, i.e. install, "
                              "compile, pull all necessary source code and libraries")

    gr_plan.add_argument("--packer", choices=packers.packers.keys(), default=None, required=True,
                         help="Select the packer used to pack up the built project")
    gr_plan.add_argument("--store", choices=stores.stores.keys(), default=None, required=True,
                         help="Select the store used to store the packed up project")
    gr_plan.add_argument("--gopythongo-path", dest="gopythongo_path", default=None,
                         help="Path to a virtual environment that contains GoPythonGo or a PEX GoPythonGo executable. "
                              "This will be mounted into the build environment")
    gr_plan.add_argument("--debug-noexec", dest="debug_noexec", action="store_true", default=False,
                         help="Setting this will prevent GoPythonGo from executing any commands. The command-line "
                              "will instead be printed to stdout for debugging purposes")
    gr_plan.add_argument("--eatmydata", dest="eatmydata", action="store_true", default=False,
                         help="Setting this will make GoPythonGo run each command through 'eatmydata', which will "
                              "prevent fsync calls during the build. This can significantly speed up subprocesses like "
                              "dpkg, but it can eat your data. As you typically abandon failed builds, this should "
                              "be fairly save to set")
    gr_plan.add_argument("--eatmydata-path", dest="eatmydata_executable", default="/usr/bin/eatmydata",
                         help="Specify an alternative eatmydata executable (only used if you set --eatmydata)")

    gr_out = parser.add_argument_group("Output options")
    gr_out.add_argument("-v", "--verbose", dest="verbose", default=False, action="store_true",
                        help="more output")
    gr_out.add_argument("-V", "--version", action="version", version=gopythongo.program_version)
    gr_out.add_argument("--no-color", dest="no_color", action="store_true", default=False,
                        help="Do not use ANSI color sequences in output")
    gr_out.add_argument("--debug-config", action=DebugConfigAction)

    # This parameter signals to GoPythonGo that it is running inside the build environment,
    # you will likely never have to use this parameter yourself. It is used by GoPythonGo
    # internally
    parser.add_argument("--inner", dest="is_inner", action="store_true", default=False,
                        help=argparse.SUPPRESS)
    # serialized version as read by the Versioner and parsed by the Version Parser outside of the build environment
    parser.add_argument("--inner-vin", dest="inner_vin", default=None, help=argparse.SUPPRESS)
    # serialized version as modified by the output Version Parser outside of the build environment
    parser.add_argument("--inner-vout", dest="inner_vout", default=None, help=argparse.SUPPRESS)

    return parser


def validate_args(args: argparse.Namespace) -> None:
    if not args.builder:
        raise ErrorMessage("You must select a builder using --builder.")
    if not args.packer:
        raise ErrorMessage("You must select a packer using --packer.")
    if not args.store:
        raise ErrorMessage("You must select a store using --store.")

    if args.is_inner:
        if not args.inner_vin or not args.inner_vout:
            raise ErrorMessage("When GoPythonGo runs inside a build environment, marked by %s, then %s and %s %s also "
                               "both be present." % (highlight("--inner"), highlight("--inner-vin"),
                                                     highlight("--inner-vout"), highlight("MUST")))

    if args.eatmydata:
        if not os.path.exists(args.eatmydata_executable) or not os.access(args.eatmydata_executable, os.X_OK):
            print_warning("%s is set, but %s is not an executable" %
                          (highlight("--eatmydata"), highlight(args.eatmydata_executable)))
            print_warning("Make sure that eatmydata is available *inside* your build environment as well, if you want "
                          "to use it to speed up the build process inside the environment.")

    for subvalidate in [initializers.validate_args, builders.validate_args, versioners.validate_args,
                        assemblers.validate_args, packers.validate_args, stores.validate_args]:
        subvalidate(args)


def print_help() -> None:
    print("Usage: python -m gopythongo.main (--help|--init [folder]|-c [configfile])\n"
          "\n"
          "While the command-line interface provides a useful reference and can be\n"
          "used for testing and development, you really want to put all build\n"
          "instructions into a .gopythongo folder inside your project. The default\n"
          "config file name is .gopythongo/config.\n"
          "\n"
          "    --help           Run \"python -m gopythongo.main --help\" to get more help\n"
          "    --init [folder]  Run \"python -m gopythongo.main --init\" to create a basic\n"
          "                     configuration in a folder (Default: .gopythongo/)\n"
          "    -c [configfile]  Run GoPythonGo as configured by 'configfile'.\n"
          "                     (Default: .gopythongo/config)\n"
          "\n"
          "You can also find more information at http://gopythongo.com/.\n")


def _sigint_handler(sig: int, frame: FrameType) -> None:
    print_warning("CTRL+BREAK. Exiting.")
    sys.exit(1)


def _cleanup_tempfiles() -> None:
    if tempfiles:
        print_info("Cleaning up temporary files...")
        for f in tempfiles:
            if os.path.exists(f):
                os.unlink(f)


def route() -> None:
    atexit.register(_cleanup_tempfiles)
    signal.signal(signal.SIGINT, _sigint_handler)

    for subinit in [initializers.init_subsystem, versioners.init_subsystem, builders.init_subsystem,
                    assemblers.init_subsystem, packers.init_subsystem, stores.init_subsystem]:
        subinit()

    if len(sys.argv) > 1:
        args = get_parser().parse_args()
        init_color(args.no_color)

        validate_args(args)

        if args.eatmydata and os.path.exists(args.eatmydata_executable) and \
                os.access(args.eatmydata_executable, os.X_OK):
            utils.prepend_exec = [args.eatmydata_executable]

        utils.debug_donotexecute = args.debug_noexec
        utils.enable_debug_output = args.verbose

        if not args.is_inner:
            # STEP 1: Start the build, which will execute gopythongo.main --inner for step 2
            versioners.version(args)
            builders.build(args)

            # STEP 3: After the 2nd gopythongo process is finished, we end up here
            stores.store(args)
        else:
            # STEP 2: ... which will land here and execute inside the build environment
            assemblers.assemble(args)
            packers.pack(args)

    else:
        print_help()


def main() -> None:
    try:
        route()
    except ErrorMessage as e:
        print_error("%s" % e.ansi_msg)
        if utils.enable_debug_output:
            raise
        else:
            sys.exit(e.exitcode)


if __name__ == "__main__":
    main()
