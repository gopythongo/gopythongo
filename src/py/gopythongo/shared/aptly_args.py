# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import configargparse
import os

from typing import List

from gopythongo.utils import highlight, ErrorMessage
from gopythongo.utils.debversion import DebianVersion, InvalidDebianVersionString

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

        gr_aptly_shared.add_argument("--aptly-fallback-version", dest="aptly_fallback_version", default=None,
                                     help="If the APT repository does not yet contain a package with the name "
                                          "specified by --aptly-query, the Aptly Versioner can return a fallback "
                                          "value. This is useful for fresh repositories.")
        gr_aptly_shared.add_argument("--aptly-versioner-opts", dest="aptly_versioner_opts", default="",
                                     help="Specify additional command-line parameters which will be appended to every "
                                          "invocation of aptly by the Aptly Versioner.")
        gr_aptly_shared.add_argument("--aptly-query", dest="aptly_query", default=None,
                                     help="Set the query to run on the aptly repo. For example: get the latest "
                                          "revision of a specific version through --aptly-query='Name ([yourpackage]), "
                                          "$Version (>=0.9.5), Version (<=0.9.6)'). More information on the query "
                                          "syntax can be found on https://aptly.info. To find the overall latest "
                                          "version of GoPythonGo in a repo, you would use "
                                          "--aptly-query='Name (gopythongo)'")
    _aptly_shared_args_added = True


def validate_shared_args(args: configargparse.Namespace) -> None:
    if not os.path.exists(args.aptly_executable) or not os.access(args.aptly_executable, os.X_OK):
        raise ErrorMessage("aptly not found in path or not executable (%s). You can specify "
                           "an alternative path using %s" %
                           (args.aptly_executable, highlight("--use-aptly")))

    if not args.aptly_repo:
        raise ErrorMessage("To use the aptly Versioner or Store, you MUST provide the name of the aptly repository to "
                           "operate on via %s" % highlight("--repo"))

    if args.aptly_fallback_version:
        try:
            DebianVersion.fromstring(args.aptly_fallback_version)
        except InvalidDebianVersionString as e:
            raise ErrorMessage("The fallback version string you specified via %s is not a valid Debian version "
                               "string. (%s)" % (highlight("--fallback-version"), str(e))) from e

    if not args.aptly_query:
        raise ErrorMessage("To use the Aptly Versioner, you must specify --aptly-query.")


def get_aptly_cmdline(args: configargparse.Namespace, *, override_aptly_cmd: str=None) -> List[str]:
    if override_aptly_cmd:
        cmdline = [override_aptly_cmd]
    else:
        cmdline = [args.aptly_executable]

    if args.aptly_config:
        cmdline += ["-config", args.aptly_config]

    return cmdline
