# -* encoding: utf-8 *-
import os
import argparse

from typing import Any

from gopythongo.utils import highlight, ErrorMessage
from gopythongo.versioners import BaseVersioner


class BumpVersioner(BaseVersioner):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versioner_name(self) -> str:
        return u"bumpversion"

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        gr_bv = parser.add_argument_group("Bumpversion Versioner options")
        gr_bv.add_argument("--use-bumpversion", dest="bumpversion_executable", default=None,
                           help="Set the path to the bumpversion shellscript. Required if you want to use the "
                                "bumpversion Versioner.")
        gr_bv.add_argument("--bumpversion-part", dest="bumpversion_part", default=None,
                           help="Select the part of the version string that you want to bump.")
        gr_bv.add_argument("--bumpversion-file", dest="bumpversion_file", action="append", default=[],
                           help="List the files that bumpversion should modify.")
        gr_bv.add_argument("--bumpversion-opts", dest="bumpversion_opts", action="append", default=[],
                           help="Additional arbitrary command-line options to pass to bumpversion.")

    def validate_args(self, args: argparse.Namespace) -> None:
        if not args.bumpversion_executable:
            raise ErrorMessage("To use the bumpversion Versioner, you must set %s" % highlight("--use-bumpversion"))

        if not os.path.exists(args.bumpversion_executable) or not os.access(args.bumpversion_executable, os.X_OK):
            raise ErrorMessage("%s (from %s) does not exist or is not executable" %
                               (highlight(args.bumpversion_executable), highlight("--use-bumpversion")))

        if not args.bumpversion_part:
            raise ErrorMessage("To use the bumpversion Versioner, you must specify the version string part to bump "
                               "(%s)" % highlight("--bumpversion-part"))

        for f in args.bumpversion_file:
            if not os.path.exists(f):
                raise ErrorMessage("File not found: Trying to run bumpversion on a non-existent file %s" % f)

    @property
    def can_read(self) -> bool:
        return True

    def read(self, args: argparse.Namespace) -> str:
        pass

    def print_help(self) -> None:
        print("Bumpversion integration\n"
              "=======================\n"
              "\n"
              "Using the bumpversion Versioner makes it easy to integrate versioning into your\n"
              "development workflow. GoPythonGo will execute bumpversion for you and read the\n"
              "output version strings. While you can use bumpversions version control\n"
              "integration, it might not be a good idea to run it automatically from\n"
              "GoPythonGo.\n"
              "\n"
              "You can find good information on using bumpversion here:\n"
              "  http://kylepurdon.com/blog/a-python-versioning-workflow-with-bumpversion.html\n")


versioner_class = BumpVersioner
