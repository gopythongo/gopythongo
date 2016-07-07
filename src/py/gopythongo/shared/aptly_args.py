# -* encoding: utf-8 *-
import os
import argparse

from typing import List

from gopythongo.utils import highlight, ErrorMessage


_aptly_shared_args_added = False  # type: bool


def add_shared_args(parser: argparse.ArgumentParser) -> None:
    global _aptly_shared_args_added

    if not _aptly_shared_args_added:
        gr_aptly_shared = parser.add_argument_group("Aptly shared options (Store and Versioners)")
        gr_aptly_shared.add_argument("--use-aptly", dest="aptly_executable", default="/usr/bin/aptly",
                                     help="The full path to the aptly executable to use")
        gr_aptly_shared.add_argument("--aptly-config", dest="aptly_config", default=None,
                                     help="Path to the aptly config file to use")
        gr_aptly_shared.add_argument("--repo", dest="aptly_repo", default=None,
                                     help="Name of the aptly repository to place the package in. (This must be "
                                          "accessible from the builder environment to be useful.)")

    _aptly_shared_args_added = True


def validate_shared_args(args: argparse.Namespace) -> None:
    if not os.path.exists(args.aptly_executable) or not os.access(args.aptly_executable, os.X_OK):
        raise ErrorMessage("aptly not found in path or not executable (%s). You can specify "
                           "an alternative path using %s" %
                           (args.aptly_executable, highlight("--use-aptly")))


def get_aptly_cmdline(args: argparse.Namespace) -> List[str]:
    cmdline = [args.aptly_executable]

    if args.aptly_config:
        cmdline += ["-config", args.aptly_config]

    return cmdline
