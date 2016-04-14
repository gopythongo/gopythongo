# -* encoding: utf-8 *-

import os
import sys

from gopythongo.builders import docker, pbuilder
from gopythongo.utils import print_error

modules = {
    "pbuilder": pbuilder,
    "docker": docker,
}


def add_args(parser):
    gr_bundle = parser.add_argument_group("Bundle settings")
    gr_bundle.add_argument("--virtualenv-binary", dest="virtualenv_binary", default="/usr/bin/virtualenv",
                           help="set an alternative virtualenv binary to use inside the builder container")

    for m in modules.values():
        m.add_args(parser)

    return parser


def validate_args(args):
    if args.builder:
        if args.builder in modules.keys():
            modules[args.builder].validate_args(args)

    if not os.path.exists(args.virtualenv_binary) or not os.access(args.virtualenv_binary, os.X_OK):
        print_error("virtualenv binary does not exist or is not executable in path %s" % args.virtualenv_binary)
        sys.exit(1)


def build(args):
    modules[args.builder].build(args)
