# -* encoding: utf-8 *-
import argparse

from typing import List, Any

import gopythongo.shared.aptly_args as _aptly_args

from gopythongo.versioners import BaseVersioner
from gopythongo.utils.debversion import DebianVersion, InvalidDebianVersionString
from gopythongo.utils import highlight, run_process, ErrorMessage
from gopythongo.versioners.parsers import VersionContainer


class AptlyVersioner(BaseVersioner):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versioner_name(self) -> str:
        return u"aptly"

    @property
    def can_read(self) -> bool:
        return True

    def can_execute_action(self, action: str) -> bool:
        if action in ["increment-epoch-if-exists", "increment-revision-if-exists"]:
            return True
        return False

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

    def validate_args(self, args: argparse.Namespace) -> None:
        _aptly_args.validate_shared_args(args)

        if args.aptly_fallback_version:
            try:
                DebianVersion.fromstring(args.aptly_fallback_version)
            except InvalidDebianVersionString as e:
                raise ErrorMessage("The fallback version string you specified via %s is not a valid Debian version "
                                   "string. (%s)" % (highlight("--fallback-version"), str(e))) from e

        if not args.package_name:
            raise ErrorMessage("To use the Aptly Versioner, you must specify --package-name.")

    def read(self, args: argparse.Namespace) -> str:
        cmd = _aptly_args.get_aptly_cmdline(args)

        if args.aptly_versioner_opts:
            cmd += args.aptly_versioner_opts

        cmd += ["package", "search", "-format=\"{{.Version}}\"", args.package_name]

        output = run_process(*cmd)
        # TODO: parse output


versioner_class = AptlyVersioner
