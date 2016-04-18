# -* encoding: utf-8 *-

import os
import sys

from gopythongo.builders import docker, pbuilder
from gopythongo.utils import print_error, highlight

modules = {
    "pbuilder": pbuilder,
    "docker": docker,
}


def add_args(parser):
    gr_bundle = parser.add_argument_group("Bundle settings")
    gr_bundle.add_argument("--use-virtualenv", dest="virtualenv_binary", default="/usr/bin/virtualenv",
                           help="Set an alternative virtualenv binary to use inside the builder container")
    gr_bundle.add_argument("--mount", dest="mounts", action="append", default=[],
                           help="Additional folders to mount into the build environment. Use "
                                "\"hostfolder:mountdestination\" syntax to mount the folder in a different place.")

    for m in modules.values():
        m.add_args(parser)

    return parser


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


def build(args):
    modules[args.builder].build(args)
