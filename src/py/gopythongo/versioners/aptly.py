# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import configargparse

from typing import List, Any, Type

import gopythongo.shared.aptly_args as _aptly_args

from gopythongo.versioners import BaseVersioner
from gopythongo.utils.debversion import DebianVersion, InvalidDebianVersionString
from gopythongo.utils import highlight, run_process, ErrorMessage, print_info, flatten, cmdargs_unquote_split


class AptlyVersioner(BaseVersioner):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versioner_name(self) -> str:
        return u"aptly"

    @property
    def can_read(self) -> bool:
        return True

    def print_help(self) -> None:
        pass

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        _aptly_args.add_shared_args(parser)

        gr_aptly = parser.add_argument_group("Aptly Versioner options")
        gr_aptly.add_argument("--aptly-fallback-version", dest="aptly_fallback_version", default=None,
                              help="If the APT repository does not yet contain a package with the name specified by "
                                   "--aptly-query, the Aptly Versioner can return a fallback value. This is useful "
                                   "for fresh repositories.")
        gr_aptly.add_argument("--aptly-versioner-opts", dest="aptly_versioner_opts", default="",
                              help="Specify additional command-line parameters which will be appended to every "
                                   "invocation of aptly by the Aptly Versioner.")
        gr_aptly.add_argument("--aptly-query", dest="aptly_query", default=None,
                              help="Set the query to run on the aptly repo. For example: get the latest revision of a "
                                   "specific version through --aptly-query='Name ([yourpackage]), $Version (>=0.9.5), "
                                   "Version (<=0.9.6)'). More information on the query syntax can be found on "
                                   "https://aptly.info. To find the overall latest version of GoPythonGo in a repo, "
                                   "you would use --aptly-query='Name (gopythongo)'")

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
        cmd = _aptly_args.get_aptly_cmdline(args) + ["repo", "search"]
        cmd += cmdargs_unquote_split(args.aptly_versioner_opts)

        cmd += ["-format", "{{.Version}}", args.aptly_repo, query]
        ret = run_process(*cmd, allow_nonzero_exitcode=True)
        # FIXME: add error code handling, because no results is not the only possible error message
        # FIXME: There can only be one instance of a package in an APT repo
        if ret.exitcode != 0 and "ERROR: no results" in ret.output:
            if allow_fallback_version and args.aptly_fallback_version:
                return [DebianVersion.fromstring(args.aptly_fallback_version)]
            else:
                return []
        elif ret.exitcode != 0:
            # we must have run into a problem
            raise ErrorMessage("aptly reported an unknown problem with exit code %s\n*** Output follows:\n%s" %
                               (ret.exitcode, highlight(ret.output) if ret.output else "no output"))
        else:
            versions = []  # type: List[DebianVersion]
            for line in ret.output.split():
                line = line.strip()
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
        versions = self.query_repo_versions(args.aptly_query, args, allow_fallback_version=True)

        if not versions:
            raise ErrorMessage("The Aptly Versioner was unable to find a base version using the specified query '%s'. "
                               "If the query is correct, you should specify a fallback version using %s." %
                               (highlight(args.aptly_query), highlight("--fallback-version")))

        return str(versions[-1])


versioner_class = AptlyVersioner  # type: Type[AptlyVersioner]
