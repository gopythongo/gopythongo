# -* encoding: utf-8 *-

import gopythongo.main
import subprocess
import sys
import os

from gopythongo.builders import docker, pbuilder
from gopythongo.utils import print_error, print_info, highlight, create_script_path, print_warning, plugins
from gopythongo.utils.buildcontext import the_context

builders = {
    "pbuilder": pbuilder,
    "docker": docker,
}


def add_args(parser):
    global builders

    try:
        plugins.load_plugins("gopythongo.builders", builders, "builder_name",
                             ["add_args", "validate_args", "build"])
    except ImportError as e:
        print_error(e.message)
        sys.exit(1)

    gr_bundle = parser.add_argument_group("Bundle settings")
    gr_bundle.add_argument("--use-virtualenv", dest="virtualenv_binary", default="/usr/bin/virtualenv",
                           help="Set an alternative virtualenv binary to use inside the builder container")
    gr_bundle.add_argument("--mount", dest="mounts", action="append", default=[],
                           help="Additional folders to mount into the build environment. Due to limitations of "
                                "the builders all paths will be mounted in place, i.e. in the same location where they "
                                "exist on the host system.")

    for b in builders.values():
        b.add_args(parser)

    return parser


class NoMountableGoPythonGo(Exception):
    pass


def _test_gopythongo_version(cmd):
    try:
        output = subprocess.check_output(cmd).decode("utf-8").strip()
        if output == gopythongo.__version__:
            return True
        if len(output) >= 10 and output[:10] == gopythongo.__version__[:10]:
            print_error("%s is GoPthonGo, but a different version (%s vs. %s)" %
                        (highlight(cmd[0]), highlight(output[11:]), highlight(gopythongo.__version__[11:])))
            raise NoMountableGoPythonGo("Mixed GoPythonGo versions")
    except subprocess.CalledProcessError as e:
        print_error("Error when trying to find out GoPythonGo version of nested executable")
        print_error(e.message)
        raise NoMountableGoPythonGo("Error when trying to get GoPythonGo version")

    raise NoMountableGoPythonGo("Found something, but it's not GoPythonGo? (%s)" % output)


def test_gopythongo(path):
    """
    :returns: (str, list) -- A tuple containing the base path of the virtualenv/executable and a list containing
                             the executable and a list of command-line parameters necessary to execute GoPythonGo,
                             which can be passed to subprocess.Popen
    """
    if os.path.isfile(path):
        if os.access(path, os.X_OK):
            # path might be a PEX executable
            print_info("We found what is presumably a PEX executable in %s" % highlight(path))
            try:
                if _test_gopythongo_version([path, "--version"]):
                    return os.path.dirname(path), [path]
            except NoMountableGoPythonGo as e:
                print_error(e)
                sys.exit(1)

    elif os.path.isdir(path):
        if os.access(create_script_path(path, "python"), os.X_OK):
            print_info("We found what is presumably a virtualenv in %s" % highlight(path))
            try:
                if _test_gopythongo_version([create_script_path(path, "python"), "-m", "gopythongo.main", "--version"]):
                    return path, [create_script_path(path, "python"), "-m", "gopythongo.main"]
            except NoMountableGoPythonGo as e:
                print_error(e)
                sys.exit(1)
    raise NoMountableGoPythonGo("Can't find GoPythonGo as a virtualenv or PEX executable in %s" % path)


def validate_args(args):
    if args.builder:
        if args.builder in builders.keys():
            builders[args.builder].validate_args(args)

    if not os.path.exists(args.virtualenv_binary) or not os.access(args.virtualenv_binary, os.X_OK):
        print_error("virtualenv not found in path or not executable (%s).\n"
                    "You can specify an alternative path with %s" %
                    (args.virtualenv_binary, highlight("--use-virtualenv")))
        sys.exit(1)

    for mount in args.mounts:
        if not os.path.exists(mount):
            print_error("Folder to be mounted does not exist:\n%s" % highlight(mount))
            sys.exit(1)

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
            args.mounts.append(the_context.gopythongo_path)

    if not gpg_path_found:
        test_path = os.path.dirname(os.path.dirname(sys.executable))

        try:
            the_context.gopythongo_path, the_context.gopythongo_cmd = test_gopythongo(test_path)
        except NoMountableGoPythonGo as e:
            pass
        else:
            print_info("Propagating GoPythonGo to build environment from detected path %s" % (highlight(test_path)))
            args.mounts.append(the_context.gopythongo_path)
            gpg_path_found = True

    if not gpg_path_found:
        print_error("Can't detect GoPythonGo path. You should run GoPythonGo from a virtualenv.")
        sys.exit(1)


def build(args):
    builders[args.builder].build(args)
