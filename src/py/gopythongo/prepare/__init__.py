#!/usr/bin/python -u
# -* encoding: utf-8 *-

from gopythongo.prepare import docker, pbuilder

_args = None

modules = {
    "pbuilder": pbuilder,
    "docker": docker,
}


def add_parser(subparsers):
    parser = subparsers.add_parser(name="prepare",
                                   description="",
                                   help="gopythongo.main prepare")

    pos_args = parser.add_argument_group("Positional arguments")
    pos_args.add_argument("build_path",
                          help="set the location where the virtual environment will be built, this " +
                               "is IMPORTANT as it is also the location where the virtualenv must " +
                               "ALWAYS reside (i.e. the install directory. Virtualenvs are NOT relocatable" +
                               "by default! All path parameters are relative to this path.")
    pos_args.add_argument("packages", metavar="package<=>version", nargs="+",
                          help="a list of package/version specifiers. Remember to quote your " +
                               "strings as in \"Django>=1.6,<1.7\"")

    gr_bundle = parser.add_argument_group("Bundle settings")
    gr_bundle.add_argument("--virtualenv-binary", dest="virtualenv_binary",
                           help="set an alternative virtualenv binary to use",
                           default="/usr/bin/virtualenv")

    for m in modules.values():
        m.add_args(parser)

    return parser


def validate_args(args):
    pass


def main(args):
    global _args
    validate_args(args)

    print('***')


if __name__ == "__main__":
    main()
