#!/usr/bin/python -u
# -* encoding: utf-8 *-

import gopythongo.main
from gopythongo.prepare import docker, pbuilder

from configargparse import ArgParser as ArgumentParser


_args = None


def get_parser():
    parser = ArgumentParser(description="Build a Python virtualenv deployment artifact and collect "
                                        "a Django project's static content if needed. The created "
                                        "virtualenv is ready to be deployed to a server. "
                                        "This tool is designed to be used with pbuilder so it can build a virtual "
                                        "environment in the path where it will be deployed within a chroot. "
                                        "Paramters that start with '--' (eg. --mode) can "
                                        "also be set in a config file (.gopythongo) by using .ini or .yaml-style "
                                        "syntax (eg. mode=value). If a parameter is specified in more than one place, "
                                        "then command-line values override config file values which override defaults. "
                                        "More information at http://gopythongo.com/.",
                            fromfile_prefix_chars="@",
                            default_config_files=["./.gopythongo"],
                            add_config_file_help=False,
                            prog="gopythongo.main prepare")

    pos_args = parser.add_argument_group("Positional arguments")
    pos_args.add_argument("build_path",
                          help="set the location where the virtual environment will be built, this " +
                               "is IMPORTANT as it is also the location where the virtualenv must " +
                               "ALWAYS reside (i.e. the install directory. Virtualenvs are NOT relocatable" +
                               "by default! All path parameters are relative to this path.")
    pos_args.add_argument("packages", metavar="package<=>version", nargs="+",
                          help="a list of package/version specifiers. Remember to quote your " +
                               "strings as in \"Django>=1.6,<1.7\"")

    parser = gopythongo.main.add_common_parameters_to_parser(parser)

    gr_bundle = parser.add_argument_group("Bundle settings")
    gr_bundle.add_argument("--virtualenv-binary", dest="virtualenv_binary",
                           help="set an alternative virtualenv binary to use",
                           default="/usr/bin/virtualenv")

    return parser


def validate_args(args):
    pass


def parse_args():
    global _args
    parser = get_parser()
    _args = parser.parse_args()
    validate_args(_args)


def main():
    global _args
    parse_args()

    print('***')


if __name__ == "__main__":
    main()
