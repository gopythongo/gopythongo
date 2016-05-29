# -* encoding: utf-8 *-

import sys
import os

from gopythongo.utils import highlight, print_error

_aptly_shared_args_added = False


def add_shared_args(parser):
    global _aptly_shared_args_added

    if not _aptly_shared_args_added:
        gr_aptly_shared = parser.add_argument_group("Aptly common parameters")
        gr_aptly_shared.add_argument("--use-aptly", dest="aptly_executable", default="/usr/bin/aptly",
                                     help="The full path to the aptly executable to use")
        gr_aptly_shared.add_argument("--aptly-config", dest="aptly_config", default=None,
                                     help="Path to the aptly config file to use")
        gr_aptly_shared.add_argument("--repo", dest="repo", default=None,
                                     help="Name of the aptly repository to place the package in. (This must be "
                                          "accessible from the builder environment to be useful.)")

    _aptly_shared_args_added = True


def validate_shared_args(args):
    if not os.path.exists(args.aptly_executable) or not os.access(args.aptly_executable, os.X_OK):
        print_error("aptly not found in path or not executable (%s). You can specify "
                    "an alternative path using %s" % (args.aptly_executable,
                                                      highlight("--use-aptly")))
        sys.exit(1)


def get_aptly_cmdline(args):
    cmdline = [args.aptly_executable]

    if args.aptly_config:
        cmdline += ["-config", args.aptly_config]

    return cmdline
