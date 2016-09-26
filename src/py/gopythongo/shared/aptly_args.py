# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import configargparse
import os

from typing import List

from gopythongo.utils import highlight, ErrorMessage


_aptly_shared_args_added = False  # type: bool


def add_shared_args(parser: configargparse.ArgumentParser) -> None:
    global _aptly_shared_args_added

    if not _aptly_shared_args_added:
        gr_aptly_shared = parser.add_argument_group("Aptly shared options (Store and Versioners)")
        gr_aptly_shared.add_argument("--use-aptly", dest="aptly_executable", default="/usr/bin/aptly",
                                     env_var="APTLY_EXECUTABLE",
                                     help="The full path to the aptly executable to use")
        gr_aptly_shared.add_argument("--aptly-config", dest="aptly_config", default=None, env_var="APTLY_CONFIG",
                                     help="Path to the aptly config file to use")
        gr_aptly_shared.add_argument("--repo", dest="aptly_repo", default=None, env_var="REPO",
                                     help="Name of the aptly repository to place the package in.")

    _aptly_shared_args_added = True


def validate_shared_args(args: configargparse.Namespace) -> None:
    if not os.path.exists(args.aptly_executable) or not os.access(args.aptly_executable, os.X_OK):
        raise ErrorMessage("aptly not found in path or not executable (%s). You can specify "
                           "an alternative path using %s" %
                           (args.aptly_executable, highlight("--use-aptly")))

    if not args.aptly_repo:
        raise ErrorMessage("To use the aptly Versioner or Store, you MUST provide the name of the aptly repository to "
                           "operate on via %s" % highlight("--repo"))


def get_aptly_cmdline(args: configargparse.Namespace, *, override_aptly_cmd: str=None) -> List[str]:
    if override_aptly_cmd:
        cmdline = [override_aptly_cmd]
    else:
        cmdline = [args.aptly_executable]

    if args.aptly_config:
        cmdline += ["-config", args.aptly_config]

    return cmdline
