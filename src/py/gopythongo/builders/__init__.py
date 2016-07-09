# -* encoding: utf-8 *-
import argparse
import subprocess
import sys
import os

from typing import Dict, List, Tuple, Any

import gopythongo
from gopythongo.utils import print_info, highlight, create_script_path, print_warning, plugins, \
                             CommandLinePlugin, ErrorMessage
from gopythongo.utils.buildcontext import the_context


builders = {}  # type: Dict[str, 'BaseBuilder']


def init_subsystem() -> None:
    global builders

    from gopythongo.builders import docker, pbuilder
    builders = {
        u"pbuilder": pbuilder.builder_class(),
        u"docker": docker.builder_class(),
    }

    plugins.load_plugins("gopythongo.builders", builders, "builder_class", BaseBuilder, "builder_name")


class BaseBuilder(CommandLinePlugin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def builder_name(self) -> str:
        """
        **@property**
        """
        raise NotImplementedError("Each subclass of BaseBuilder MUST implement builder_name")

    def build(self, args: argparse.Namespace) -> None:
        pass


def add_args(parser: argparse.ArgumentParser) -> None:
    global builders

    gr_bundle = parser.add_argument_group("Bundle settings")
    gr_bundle.add_argument("--mount", dest="mounts", action="append", default=[],
                           help="Additional folders to mount into the build environment. Due to limitations of "
                                "the builders all paths will be mounted in place, i.e. in the same location where they "
                                "exist on the host system.")

    for b in builders.values():
        b.add_args(parser)


class NoMountableGoPythonGo(ErrorMessage):
    pass


def _test_gopythongo_version(cmd: List[str]) -> bool:
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).strip().decode("utf-8")
        if output == gopythongo.program_version:
            return True
        if len(output) >= 10 and output[:10] == gopythongo.program_version[:10]:
            raise NoMountableGoPythonGo("Mixed versions! %s is GoPthonGo, but a different version (%s vs. %s)" %
                                        (highlight(cmd[0]), highlight(output[11:]),
                                         highlight(gopythongo.program_version[11:])))
    except subprocess.CalledProcessError as e:
        raise NoMountableGoPythonGo("Error when trying to find out GoPythonGo version of nested executable. %s" %
                                    str(e)) from e

    raise NoMountableGoPythonGo("Found something, but it's not GoPythonGo? (%s)" % output)


def test_gopythongo(path: str) -> Tuple[str, List[str]]:
    """
    :returns: (str, list) -- A tuple containing the base path of the virtualenv/executable and a list containing
                             the executable and a list of command-line parameters necessary to execute GoPythonGo,
                             which can be passed to subprocess.Popen
    """
    if os.path.isfile(path):
        if os.access(path, os.X_OK):
            # path might be a PEX executable
            print_info("We found what is presumably a PEX executable in %s" % highlight(path))
            if _test_gopythongo_version([path, "--version"]):
                return os.path.dirname(path), [path]

    elif os.path.isdir(path):
        if os.access(create_script_path(path, "python"), os.X_OK):
            print_info("We found what is presumably a virtualenv in %s" % highlight(path))
            if _test_gopythongo_version([create_script_path(path, "python"), "-m", "gopythongo.main", "--version"]):
                return path, [create_script_path(path, "python"), "-m", "gopythongo.main"]
    raise NoMountableGoPythonGo("Can't find GoPythonGo as a virtualenv or PEX executable in %s" % path)


def validate_args(args: argparse.Namespace) -> None:
    if args.builder:
        if args.builder in builders.keys():
            builders[args.builder].validate_args(args)

    if not os.path.exists(args.virtualenv_binary) or not os.access(args.virtualenv_binary, os.X_OK):
        raise ErrorMessage("virtualenv not found in path or not executable (%s).\n"
                           "You can specify an alternative path with %s" %
                           (args.virtualenv_binary, highlight("--use-virtualenv")))

    for mount in args.mounts:
        if not os.path.exists(mount):
            raise ErrorMessage("Folder to be mounted does not exist: %s" % highlight(mount))

    gpg_path_found = False
    if os.getenv("VIRTUAL_ENV"):
        try:
            the_context.gopythongo_path, the_context.gopythongo_cmd = test_gopythongo(os.getenv("VIRTUAL_ENV"))
        except NoMountableGoPythonGo as e:
            print_warning("$VIRTUAL_ENV is set, but does not point to a virtual environment with GoPythonGo?")
        else:
            print_info("Propagating GoPythonGo to build environment from $VIRTUAL_ENV %s" %
                       (highlight(os.getenv("VIRTUAL_ENV"))))
            gpg_path_found = True
            the_context.mounts.add(the_context.gopythongo_path)

    if not gpg_path_found:
        test_path = os.path.dirname(os.path.dirname(sys.executable))

        try:
            the_context.gopythongo_path, the_context.gopythongo_cmd = test_gopythongo(test_path)
        except NoMountableGoPythonGo as e:
            pass
        else:
            print_info("Propagating GoPythonGo to build environment from detected path %s" % (highlight(test_path)))
            the_context.mounts.add(the_context.gopythongo_path)
            gpg_path_found = True

    if not gpg_path_found:
        raise ErrorMessage("Can't detect GoPythonGo path. You should run GoPythonGo from a virtualenv.")


def build(args: argparse.Namespace) -> None:
    builders[args.builder].build(args)
