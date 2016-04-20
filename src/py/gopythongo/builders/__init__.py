# -* encoding: utf-8 *-

import os
import sys

from gopythongo.builders import docker, pbuilder
from gopythongo.utils import print_error, print_info, highlight, create_script_path, BUILDCTX

modules = {
    "pbuilder": pbuilder,
    "docker": docker,
}


def add_args(parser):
    gr_bundle = parser.add_argument_group("Bundle settings")
    gr_bundle.add_argument("--use-virtualenv", dest="virtualenv_binary", default="/usr/bin/virtualenv",
                           help="Set an alternative virtualenv binary to use inside the builder container")
    gr_bundle.add_argument("--mount", dest="mounts", action="append", default=[],
                           help="Additional folders to mount into the build environment. Due to limitations of "
                                "the builders all paths will be mounted in place, i.e. in the same location where they "
                                "exist on the host system.")

    for m in modules.values():
        m.add_args(parser)

    return parser


def test_gopythongo(path):
    # TODO: test gpg --version output for virtualenv or PEX
    pass


def validate_args(args):
    if args.builder:
        if args.builder in modules.keys():
            modules[args.builder].validate_args(args)

    if not os.path.exists(args.virtualenv_binary) or not os.access(args.virtualenv_binary, os.X_OK):
        print_error("virtualenv not found in path or not executable (%s).\n"
                    "You can specify an alternative path with %s" %
                    (args.virtualenv_binary, highlight("--use-virtualenv")))
        sys.exit(1)

    for mount in args.mounts:
        if not os.path.exists(mount):
            print_error("Folder to be mounted does not exist:\n%s" % highlight(mount))
            sys.exit(1)

    # TODO: Set BUILDCTX _home and _cmd
    gpg_path_found = False
    if os.getenv("VIRTUAL_ENV"):
        print_info("Propagating GoPythonGo to build environment from $VIRTUAL_ENV %s" %
                   (highlight(os.getenv("VIRTUAL_ENV"))))
        args.mounts.append(os.getenv("VIRTUAL_ENV"))
        BUILDCTX.gopythongo_path = os.getenv("VIRTUAL_ENV")
        gpg_path_found = True
    else:
        test_path = os.path.dirname(os.path.dirname(sys.executable))

        if not os.path.exists(create_script_path(test_path, "python")):
            print_error("Detected path %s does not contain a python executable." %
                        highlight(create_script_path(test_path, "python")))
            sys.exit(1)

        print_info("Propagating GoPythonGo to build environment from detected path %s" % (highlight(test_path)))
        args.mounts.append(test_path)
        BUILDCTX.gopythongo_path = test_path
        gpg_path_found = True

    if not gpg_path_found:
        print_error("Can't detect GoPythonGo path. You should run GoPythonGo from a virtualenv.")
        sys.exit(1)


def build(args):
    modules[args.builder].build(args)
