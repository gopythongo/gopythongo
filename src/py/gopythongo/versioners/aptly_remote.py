# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import configargparse

from typing import List, Any, Type

import aptly_api
from gopythongo.shared.aptly_base import AptlyBaseVersioner

from gopythongo.utils.debversion import DebianVersion, InvalidDebianVersionString
from gopythongo.utils import highlight, ErrorMessage, print_info


class RemoteAptlyVersioner(AptlyBaseVersioner):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versioner_name(self) -> str:
        return u"remote-aptly"

    @property
    def can_read(self) -> bool:
        return True

    def print_help(self) -> None:
        pass

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        super().add_args(parser)
        gr_aptly = parser.add_argument_group("Aptly Remote Versioner options")
        gr_aptly.add_argument("--aptly-server-url", dest="aptly_server_url", default=None,
                              help="HTTP URL or socket path pointing to the Aptly API server you want to use.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        super().validate_args(args)
        if not args.aptly_server_url:
            raise ErrorMessage("When using the remote-aptly, you must provide %s" % highlight("--aptly-server-url"))

    def query_repo_versions(self, query: str, args: configargparse.Namespace, *,
                            allow_fallback_version: bool=False) -> List[DebianVersion]:
        _aptly = aptly_api.Client(args.aptly_server_url)

        try:
            packages = _aptly.repos.search_packages(args.aptly_repo, query, detailed=True)
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


versioner_class = RemoteAptlyVersioner  # type: RemoteAptlyVersioner
