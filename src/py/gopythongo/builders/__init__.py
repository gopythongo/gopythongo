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
                           help="set an alternative virtualenv binary to use inside the builder container")

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


def build(args):
    modules[args.builder].build(args)
