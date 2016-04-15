# -* encoding: utf-8 *-

import os
import sys

from gopythongo.utils import print_error, print_info, highlight


def add_args(parser):
    gr_pbuilder = parser.add_argument_group("Pbuilder options")
    gr_pbuilder.add_argument("--use-pbuilder", dest="pbuilder_executable", default="/usr/sbin/pbuilder",
                             help="Specify an alternative pbuilder executable.")
    gr_pbuilder.add_argument("--baseenv", dest="baseenv", default=None,
                             help="Cache and reuse the pbuilder base environment. gopythongo will call pbuilder create "
                                  "on this file if it doesn't exist.")
    gr_pbuilder.add_argument("--pbuilder-force-recreate", dest="pbuilder_force_recreate", action="store_true",
                             help="Delete the base environment if it exists already.")

    gr_pbuilder.add_argument("--apt-get", dest="build_deps", action="append",
                             help="Packages to install using apt-get prior to creating the virtualenv (e.g. driver "
                                  "libs for databases so that Python C extensions compile correctly.")


def validate_args(args):
    if not os.path.exists(args.pbuilder_executable) or not os.access(args.pbuilder_executable, os.X_OK):
        print_error("pbuilder not found in path or not executable (%s).\n"
                    "You can specify an alternative path using %s" % (args.pbuilder_executable,
                                                                      highlight("--use-pbuilder")))
        sys.exit(1)


def build(args):
    print_info("Building with %s" % highlight("pbuilder"))

    # TODO: execute pbuilder create if baseenv does not exist, select temporary baseenv otherwise
