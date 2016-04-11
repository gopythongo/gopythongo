# -* encoding: utf-8 *-

from gopythongo.builders import docker, pbuilder


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
    pass
