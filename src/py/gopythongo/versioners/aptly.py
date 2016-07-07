# -* encoding: utf-8 *-
import argparse

from typing import List, Any

import gopythongo.shared.aptly_args as _aptly_args

from gopythongo.versioners import BaseVersioner
from gopythongo.utils.debversion import DebianVersion, InvalidDebianVersionString
from gopythongo.utils import highlight, run_process, ErrorMessage, print_info


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

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        _aptly_args.add_shared_args(parser)

        gr_aptly = parser.add_argument_group("Aptly Versioner options")
        gr_aptly.add_argument("--fallback-version", dest="aptly_fallback_version", default=None,
                              help="If the APT repository does not yet contain a package with the name specified by "
                                   "--package-name, the Aptly versioner can return a fallback value. This is useful "
                                   "for fresh repositories.")
        gr_aptly.add_argument("--aptly-versioner-opts", dest="aptly_versioner_opts", default=[],
                              help="Specify additional command-line parameters which will be appened to every "
                                   "invocation of aptly by the Aptly Versioner.")
        gr_aptly.add_argument("--aptly-query", dest="aptly_query", default=None,
                              help="By default the aptly Versioner will return the latest version of the package "
                                   "identified by --package-name in the repo. But sometimes you don't want that, but "
                                   "would like to, for example, get the latest revision of a specific version. You "
                                   "can do that by using --aptly-query, which will override the default. (Example: "
                                   "--aptly-query='Name (aptly), Version (>0.9.5), Version (<=0.9.6)'). More "
                                   "information on the query syntax can be found on https://aptly.info.")

    def validate_args(self, args: argparse.Namespace) -> None:
        _aptly_args.validate_shared_args(args)

        if args.aptly_fallback_version:
            try:
                DebianVersion.fromstring(args.aptly_fallback_version)
            except InvalidDebianVersionString as e:
                raise ErrorMessage("The fallback version string you specified via %s is not a valid Debian version "
                                   "string. (%s)" % (highlight("--fallback-version"), str(e))) from e

        if not args.aptly_query and not args.package_name:
            raise ErrorMessage("To use the Aptly Versioner, you must specify --package-name or --aptly-query.")

    def read(self, args: argparse.Namespace) -> str:
        cmd = _aptly_args.get_aptly_cmdline(args)

        if args.aptly_versioner_opts:
            cmd += args.aptly_versioner_opts

        package_query = args.aptly_query if args.aptly_query else args.package_name
        cmd += ["repo", "search", "-format=\"{{.Version}}\"", args.aptly_repo, package_query]

        output = run_process(*cmd).split("\n")
        if output == "ERROR: no results":
            if args.fallback_version:
                return args.fallback_version
            else:
                raise ErrorMessage("The aptly Versioner was unable to find any packages ('ERROR: no results') matching "
                                   "the package-name or query.")
        else:
            versions = []  # type: List[DebianVersion]
            for line in output:
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
                return str(versions[-1:])
            else:
                # TODO: should we return args.fallback_version instead? I think it's more useful to know the repo
                # is broken, right now.
                raise ErrorMessage("The aptly Versioner did not return a single parseable version string")


versioner_class = AptlyVersioner
