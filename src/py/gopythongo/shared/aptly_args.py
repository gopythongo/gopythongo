# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import configargparse
import os

from typing import List

from gopythongo.utils import highlight, ErrorMessage, create_script_path
from gopythongo.utils.buildcontext import the_context


_aptly_shared_args_added = False  # type: bool


def add_shared_args(parser: configargparse.ArgumentParser) -> None:
    global _aptly_shared_args_added

    if not _aptly_shared_args_added:
        gr_aptly_shared = parser.add_argument_group("Aptly shared options (Store and Versioners)")
        gr_aptly_shared.add_argument("--use-aptly", dest="aptly_executable", default="/usr/bin/aptly",
                                     env_var="APTLY_EXECUTABLE",
                                     help="The full path to the aptly executable to use when using a local aptly.")
        gr_aptly_shared.add_argument("--aptly-server-url", dest="aptly_server_url", default=None,
                                     env_var="APTLY_SERVER_URL",
                                     help="HTTP URL or socket path pointing to the Aptly API server you want to use.")
        gr_aptly_shared.add_argument("--aptly-config", dest="aptly_config", default=None, env_var="APTLY_CONFIG",
                                     help="Path to the aptly config file to use.")
        gr_aptly_shared.add_argument("--repo", dest="aptly_repo", default=None, env_var="REPO",
                                     help="Name of the aptly repository to place the package in.")

        gr_ast = parser.add_argument_group("Aptly shared options (Stores)")
        gr_ast.add_argument("--aptly-distribution", dest="aptly_distribution", default="", env_var="APTLY_DISTRIBUTION",
                            help="Set the target distribution for aptly builds.")
        gr_ast.add_argument("--aptly-publish-endpoint", dest="aptly_publish_endpoint", metavar="ENDPOINT", default=None,
                            env_var="APTLY_PUBLISH_ENDPOINT",
                            help="Publish the Aply repo to the specified endpoint after generated packages have been "
                                 "added to the repo. Please note that you will have to add additional configuration to "
                                 "the aptly config file, for example when you want to publish to S3. It's also likely "
                                 "that you want to set --aptly-publish-opts and pass aptly -passphrase-file, -keyring "
                                 "and other necessary arguments for signing the repo. Please note: You will probably "
                                 "want to set these arguments using environment variables on your build server if "
                                 "you're using a CI environment.")
        gr_ast.add_argument("--aptly-dont-remove", dest="aptly_dont_remove", action="store_true", default=False,
                            env_var="APTLY_DONT_REMOVE",
                            help="By default, if a created package already exists in the repo specified by --repo, "
                                 "the aptly store will overwrite it. Setting --aptly-dont-remove will instead lead "
                                 "to an error if the package already exists.")
        gr_ast.add_argument("--aptly-overwrite-newer", dest="aptly_overwrite_newer", action="store_true", default=False,
                            env_var="APTLY_OVERWRITE_NEWER",
                            help="If set, the aptly Store will store newly generated packages in the repo which are "
                                 "older than the packages already there. By default, it will raise an error message "
                                 "instead.")
        gr_ast.add_argument("--aptly-passphrase", dest="aptly_passphrase", env_var="APTLY_PASSPHRASE", default=None,
                            help="Set this to pass the GPG signing passphrase to the aptly Store. This is primarily "
                                 "useful when you use the environment variable. This way your build server can read "
                                 "the passphrase from secure storage it pass it to GoPythonGo with a modicum of "
                                 "protection. Using the command-line parameter however will expose the passphrase to "
                                 "every user on the system. You're better of passing --passphrase-file to aptly via "
                                 "--aptly-publish-opts in that case. The most secure option would be to use "
                                 "--use-aptly-vault-wrapper.")
        gr_ast.add_argument("--use-aptly-vault-wrapper", dest="use_aptly_wrapper", env_var="APTLY_USE_WRAPPER",
                            default=False, action="store_true",
                            help="When you set this, GoPythonGo will not directly invoke aptly to publish or update "
                                 "aptly-managed repos. Instead it will call GoPythonGo's vault_wrapper program in"
                                 "'aptly' mode, which can be configured by environment variables or its own "
                                 "configuration file or both (Default: .gopythongo/vaultwrapper). This program will "
                                 "load the GnuPG signing passphrase for aptly-managed repos from Hashicorp Vault. You "
                                 "can find out more by running 'vaultwrapper --help'.")
    _aptly_shared_args_added = True


def validate_shared_args(args: configargparse.Namespace) -> None:
    if not args.aptly_server_url and (not os.path.exists(args.aptly_executable) or
                                      not os.access(args.aptly_executable, os.X_OK)):
        raise ErrorMessage("aptly not found in path or not executable (%s) and --aptly-server-url not set. You can "
                           "specify an alternative path using %s" %
                           (args.aptly_executable, highlight("--use-aptly")))

    if not args.aptly_repo:
        raise ErrorMessage("To use the aptly Versioner or Store, you MUST provide the name of the aptly repository to "
                           "operate on via %s" % highlight("--repo"))

    if args.use_aptly_wrapper:
        wrapper_cmd = create_script_path(the_context.gopythongo_path, "vaultwrapper")
        if not os.path.exists(wrapper_cmd) or not os.access(wrapper_cmd, os.X_OK):
            raise ErrorMessage("%s can either not be found or is not executable. The vault wrapper seems to "
                               "be unavailable." % wrapper_cmd)


def get_aptly_cmdline(args: configargparse.Namespace, *, override_aptly_cmd: str=None) -> List[str]:
    if override_aptly_cmd:
        cmdline = [override_aptly_cmd]
    else:
        cmdline = [args.aptly_executable]

    if args.aptly_config:
        cmdline += ["-config", args.aptly_config]

    return cmdline
