# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from typing import Any, List

import configargparse
import gopythongo.shared.aptly_args as _aptly_args
from gopythongo.stores import BaseStore

from gopythongo.utils import ErrorMessage, highlight
from gopythongo.utils.debversion import DebianVersion, InvalidDebianVersionString
from gopythongo.versioners import BaseVersioner


class AptlyBaseVersioner(BaseVersioner):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        _aptly_args.add_shared_args(parser)
        gr_aptly_shared = parser.add_argument_group("Aptly shared options (Versioners)")
        gr_aptly_shared.add_argument("--aptly-fallback-version", dest="aptly_fallback_version", default=None,
                                     help="If the APT repository does not yet contain a package with the name "
                                          "specified by --aptly-query, the Aptly Versioner can return a fallback "
                                          "value. This is useful for fresh repositories.")
        gr_aptly_shared.add_argument("--aptly-query", dest="aptly_query", default=None,
                                     help="Set the query to run on the aptly repo. For example: get the latest "
                                          "revision of a specific version through --aptly-query='Name ([yourpackage]), "
                                          "$Version (>=0.9.5), Version (<=0.9.6)'). More information on the query "
                                          "syntax can be found on https://aptly.info. To find the overall latest "
                                          "version of GoPythonGo in a repo, you would use "
                                          "--aptly-query='Name (gopythongo)'.")

    def validate_args(self, args: configargparse.Namespace) -> None:
            _aptly_args.validate_shared_args(args)
            if args.aptly_fallback_version:
                try:
                    DebianVersion.fromstring(args.aptly_fallback_version)
                except InvalidDebianVersionString as e:
                    raise ErrorMessage("The fallback version string you specified via %s is not a valid Debian version "
                                       "string. (%s)" % (highlight("--fallback-version"), str(e))) from e

            if not args.aptly_query:
                raise ErrorMessage("To use the Aptly Versioner, you must specify --aptly-query.")

    def query_repo_versions(self, query: str, args: configargparse.Namespace, *,
                                allow_fallback_version: bool=False) -> List[DebianVersion]:
            raise NotImplementedError("Each subclass of AptlyBaseVersioner must implement query_repo_versions")

        def read(self, args: configargparse.Namespace) -> str:
            versions = self.query_repo_versions(args.aptly_query, args, allow_fallback_version=True)

            if not versions:
                raise ErrorMessage("The Aptly Versioner was unable to find a base version using the specified query '%s'. "
                                   "If the query is correct, you should specify a fallback version using %s." %
                                   (highlight(args.aptly_query), highlight("--fallback-version")))

            return str(versions[-1])


class AptlyBaseStore(BaseStore):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        _aptly_args.add_shared_args(parser)

    def validate_args(self, args: configargparse.Namespace) -> None:
        _aptly_args.validate_shared_args(args)
