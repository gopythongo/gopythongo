# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from typing import Sequence

import configargparse

from typing import List, Any, Type

import gopythongo.shared.aptly_args as _aptly_args
import aptly_api

from gopythongo.versioners import BaseVersioner
from gopythongo.utils.debversion import DebianVersion, InvalidDebianVersionString
from gopythongo.utils import highlight, ErrorMessage, print_info


class RemoteAptlyVersioner(BaseVersioner):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._aptly = None  # type: aptly_api.Client

    @property
    def versioner_name(self) -> str:
        return u"remote-aptly"

    @property
    def can_read(self) -> bool:
        return True

    def print_help(self) -> None:
        pass

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        _aptly_args.add_shared_args(parser)
        gr_aptly = parser.add_argument_group("Remote Aptly Versioner options")
        gr_aptly.add_argument("--aptly-server-url", dest="aptly_server_url", default=None,
                              help="HTTP URL or socket path pointing to the Aptly API server you want to use.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        _aptly_args.validate_shared_args(args)
        if not args.aptly_server_url:
            raise ErrorMessage("When using the remote-aptly, you must provide %s" % highlight("--aptly-server-url"))

    def query_repo_versions(self, query: str, args: configargparse.Namespace, *,
                            allow_fallback_version: bool=False) -> List[DebianVersion]:
        try:
            packages = self._aptly.repos.search_packages(args.aptly_repo, query, detailed=True)
        except aptly_api.AptlyAPIException as e:
            # we must have run into a problem
            raise ErrorMessage("aptly reported an unknown problem:\n%s" % str(e)) from e
        else:
            if len(packages) == 0:
                if allow_fallback_version and args.aptly_fallback_version:
                    return [DebianVersion.fromstring(args.aptly_fallback_version)]
                else:
                    return []

            versions = []  # type: List[DebianVersion]
            for pkg in packages:
                line = pkg.fields["Version"]
                if line:
                    try:
                        versions.append(DebianVersion.fromstring(line))
                    except InvalidDebianVersionString as e:
                        print_info("aptly returned an unparsable Debian version string. This should never happen "
                                   "in a APT repository where all versions must be valid Debian versions. (Unparseable "
                                   "return value was: %s)" % highlight(line))
            if len(versions) > 0:
                versions.sort()
                return versions
            else:
                if allow_fallback_version and args.aptly_fallback_version:
                    return [DebianVersion.fromstring(args.aptly_fallback_version)]
                else:
                    return []

    def read(self, args: configargparse.Namespace) -> str:
        self._aptly = aptly_api.Client(args.aptly_server_url)
        versions = self.query_repo_versions(args.aptly_query, args, allow_fallback_version=True)

        if not versions:
            raise ErrorMessage("The Remote Aptly Versioner was unable to find a base version using the specified "
                               "query '%s'. If the query is correct, you should specify a fallback version using %s." %
                               (highlight(args.aptly_query), highlight("--fallback-version")))

        return str(versions[-1])


versioner_class = RemoteAptlyVersioner  # type: RemoteAptlyVersioner
