#!/usr/bin/python -u
# -* encoding: utf-8 *-
import argparse

import configargparse
import shutil

import atexit
import signal
import sys
import os

from gopythongo.utils.buildcontext import the_context
from types import FrameType
from typing import List, Any, Iterable, Set, Sequence, Union

import gopythongo

from gopythongo import initializers, builders, versioners, assemblers, packers, stores, utils
from gopythongo.utils import highlight, print_error, print_warning, print_info, init_color, ErrorMessage, print_debug, \
    success

tempfiles = []  # type: List[str]
default_config_files = [".gopythongo/config"]  # type: List[str]
config_paths = set()  # type: Set[str]
args_for_setting_config_path=["-c", "--config"]  # type: List[str]


class DebugConfigAction(configargparse.Action):
    def __init__(self,
                 option_strings: List[str],
                 dest: str,
                 default: Any=None,
                 choices: Iterable[Any]=None,
                 help: str="Show all configuration keys and where they were loaded from, i.e. from the command-line, "
                           "a configuration file, or the environment") -> None:
        super().__init__(option_strings=option_strings, dest=dest, default=default,
                         nargs=0, choices=choices, help=help)

    def __call__(self, parser: configargparse.ArgumentParser, namespace: configargparse.Namespace,
                 values: Union[str, Sequence[Any], None], option_string: str=None) -> None:
        parser.print_values()
        parser.exit(0)


def get_parser() -> configargparse.ArgumentParser:
    parser = configargparse.ArgumentParser(
        description="Build a Python virtualenv deployment artifact and collect a Django project's static content if "
                    "needed. The created virtualenv is packaged and ready to be deployed to a server. This tool is "
                    "designed to be used with pbuilder or docker so it can build a virtual environment in the path "
                    "where it will be deployed. Parameters that start with '--' (eg. --builder) can also be set in a "
                    "config file (e.g. .gopythongo/config) by using .ini or .yaml-style syntax (e.g. mode=value). If a "
                    "parameter is specified in more than one place, then command-line values override config file "
                    "values which override defaults. More information at http://gopythongo.com/.",
        prog="gopythongo.main",
        args_for_setting_config_path=args_for_setting_config_path,
        config_arg_help_message="Use this path instead of the default (.gopythongo/config)",
        default_config_files=default_config_files
    )

    for subargs in [initializers.add_args, builders.add_args, versioners.add_args, assemblers.add_args,
                    packers.add_args, stores.add_args]:
        subargs(parser)

    gr_plan = parser.add_argument_group("Execution plan")
    gr_plan.add_argument("--ecosystem", dest="ecosystem", choices=["python"], default="python",
                         help="Choose the ecosystem to build from. (Default and only option right now: Python)")
    gr_plan.add_argument("--builder", dest="builder", choices=builders.get_builders().keys(), default=None,
                         required=True,
                         help="Select the builder used to build the project")

    # right now we _always_ run the virtualenv assembler (argparse will always *append* to the default list)
    # because gopythongo does not support non-python ecosystems.
    gr_plan.add_argument("--assembler", dest="assemblers",
                         choices=assemblers.get_assemblers().keys(), action="append", default=["virtualenv"],
                         help="Select one or more assemblers to build the project inside the builder, i.e. install, "
                              "compile, pull all necessary source code and libraries")

    gr_plan.add_argument("--packer", choices=packers.get_packers().keys(), default=None, required=True,
                         help="Select the packer used to pack up the built project")
    gr_plan.add_argument("--store", choices=stores.get_stores().keys(), default=None, required=True,
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
    parser.add_argument("--read-state", dest="read_state", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--cwd", dest="cwd", default=None, help=argparse.SUPPRESS)

    return parser


def validate_args(args: configargparse.Namespace) -> None:
    if not args.builder:
        raise ErrorMessage("You must select a builder using --builder.")
    if not args.packer:
        raise ErrorMessage("You must select a packer using --packer.")
    if not args.store:
        raise ErrorMessage("You must select a store using --store.")

    if args.is_inner:
        if not args.read_state or not args.cwd:
            raise ErrorMessage("When GoPythonGo runs inside a build environment, marked by %s, then %s and %s %s also "
                               "both be present." % (highlight("--inner"), highlight("--read-state"),
                                                     highlight("--cwd"), highlight("MUST")))

    if args.eatmydata:
        if not os.path.exists(args.eatmydata_executable) or not os.access(args.eatmydata_executable, os.X_OK):
            print_warning("%s is set, but %s is not an executable" %
                          (highlight("--eatmydata"), highlight(args.eatmydata_executable)))
            print_warning("Make sure that eatmydata is available *inside* your build environment as well, if you want "
                          "to use it to speed up the build process inside the environment.")

    if args.is_inner:
        # once we're in the build environment we don't want to block on features we don't need (like an missing aptly
        # executable inside
        assemblers.validate_args(args)
        packers.validate_args(args)
    else:
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


def _cleanup_tempfiles(args: configargparse.Namespace) -> None:
    if the_context.tempmount and not args.is_inner:
        if os.path.exists(the_context.tempmount):
            shutil.rmtree(the_context.tempmount)

    if tempfiles:
        for f in tempfiles:
            if os.path.exists(f):
                os.unlink(f)


def _find_default_mounts() -> Set[str]:
    global config_paths
    basepath = os.getcwd()
    miniparser = configargparse.ArgumentParser()
    miniparser.add_argument(*args_for_setting_config_path, dest="config", action="append",
                            default=[])
    args, _ = miniparser.parse_known_args()

    # type: ignore, because mypy doesn't parse add_argument above correctly
    if not args.config:
        args.config = default_config_files

    paths = set()
    paths.add(basepath)
    for cfg in args.config:
        if os.path.isfile(cfg):
            paths.add(os.path.abspath(os.path.dirname(cfg)))
            config_paths.add(os.path.dirname(cfg))
    return paths


def route() -> None:
    signal.signal(signal.SIGINT, _sigint_handler)

    for subinit in [initializers.init_subsystem, versioners.init_subsystem, builders.init_subsystem,
                    assemblers.init_subsystem, packers.init_subsystem, stores.init_subsystem]:
        subinit()

    precheck = configargparse.ArgumentParser(add_help=False)
    precheck.add_argument("--cwd", dest="cwd", default=None, help=argparse.SUPPRESS)
    preargs, _ = precheck.parse_known_args()

    if preargs.cwd:
        if not os.path.exists(preargs.cwd):
            raise ErrorMessage("GoPythonGo passed the following base path into the build environment %s, but "
                               "it seems that path doesn't exist now inside the build environment. This path "
                               "should have been mounted inside the build environment and it should exist on "
                               "the host. We can only give up." % highlight(preargs.cwd))

        os.chdir(preargs.cwd)  # This should ensure all relative paths still work (for example to --config)
        print_info("Executing in %s" % preargs.cwd)

    if len(sys.argv) > 1:
        args = get_parser().parse_args()
        atexit.register(_cleanup_tempfiles, args)
        init_color(args.no_color)

        validate_args(args)

        for mount in _find_default_mounts():
            the_context.mounts.add(mount)

        if args.eatmydata and os.path.exists(args.eatmydata_executable) and \
                os.access(args.eatmydata_executable, os.X_OK):
            utils.prepend_exec = [args.eatmydata_executable]

        utils.debug_donotexecute = args.debug_noexec
        utils.enable_debug_output = args.verbose

        if not args.is_inner:
            # STEP 1: Start the build, which will execute gopythongo.main --inner for step 2
            versioners.version(args)
            the_context.save_state()
            builders.build(args)

            # STEP 3: After the 2nd gopythongo process is finished, we end up here
            print_debug("Reading state from %s in outer shell" % highlight(the_context.state_file))
            the_context.load_state()
            stores.store(args)
        else:
            # we can't use .load_state() here because the_context doesn't know the state_file's path yet
            the_context.read(args.read_state)
            # STEP 2: ... which will land here and execute inside the build environment
            versioners.version(args)
            assemblers.assemble(args)
            packers.pack(args)
            # write the state to be read in STEP 3 above
            print_debug("Writing state to %s before returning from build environment" %
                        highlight(the_context.state_file))
            the_context.save_state()

        success("***** SUCCESS *****")
    else:
        print_help()


def main() -> None:
    try:
        route()
    except ErrorMessage as e:
        print_error("%s" % e.ansi_msg)
        if utils.enable_debug_output:
            print(highlight("********** VERBOSE OUTPUT Full Exception Follows **********"))
            raise
        else:
            sys.exit(e.exitcode)


if __name__ == "__main__":
    main()
