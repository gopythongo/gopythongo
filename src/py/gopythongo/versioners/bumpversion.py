# -* encoding: utf-8 *-
import os
import re
import shlex

import configargparse

from typing import Any, Type

from gopythongo.utils import highlight, ErrorMessage, run_process
from gopythongo.versioners import BaseVersioner


class BumpVersioner(BaseVersioner):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versioner_name(self) -> str:
        return "bumpversion"

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        gr_bv = parser.add_argument_group("Bumpversion Versioner options")
        gr_bv.add_argument("--use-bumpversion", dest="bumpversion_executable", default=None,
                           help="Set the path to the bumpversion shellscript. Required if you want to use the "
                                "bumpversion Versioner.")
        gr_bv.add_argument("--bumpversion-config", dest="bumpversion_config", default=None,
                           help="Set the path to a bumpversion config file to use.")
        gr_bv.add_argument("--bumpversion-part", dest="bumpversion_part", default=None,
                           help="Select the part of the version string that you want to bump.")
        gr_bv.add_argument("--bumpversion-file", dest="bumpversion_files", action="append", default=[],
                           help="List the files that bumpversion should modify.")
        gr_bv.add_argument("--bumpversion-opts", dest="bumpversion_opts", default="",
                           help="Additional arbitrary command-line options to pass to bumpversion.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        if not args.bumpversion_executable:
            raise ErrorMessage("To use the bumpversion Versioner, you must set %s to the bumpversion executable" %
                               highlight("--use-bumpversion"))

        if not os.path.exists(args.bumpversion_executable) or not os.access(args.bumpversion_executable, os.X_OK):
            raise ErrorMessage("%s (from %s) does not exist or is not executable" %
                               (highlight(args.bumpversion_executable), highlight("--use-bumpversion")))

        if not args.bumpversion_part:
            raise ErrorMessage("To use the bumpversion Versioner, you must specify the version string part to bump "
                               "(%s)" % highlight("--bumpversion-part"))

        for f in args.bumpversion_files:
            if not os.path.exists(f):
                raise ErrorMessage("File not found: Trying to run bumpversion on a non-existent file %s" % f)

    @property
    def can_read(self) -> bool:
        return True

    def read(self, args: configargparse.Namespace) -> str:
        bumpcmd = [args.bumpversion_executable, "--list"]

        if args.bumpversion_config:
            bumpcmd += ["--config-file", args.bumpversion_config]

        if args.bumpversion_opts:
            bumpcmd += shlex.split(args.bumpversion_opts)

        bumpcmd += [args.bumpversion_part]

        if args.bumpversion_files:
            bumpcmd += args.bumpversion_files

        ret = run_process(*bumpcmd)

        m = re.match("new_version=\"?(.*?)\"?", ret.output)
        if m:
            return m.group(1)
        else:
            raise ErrorMessage("GoPythonGo was unable to read the new_version output from bumpversion for some reason, "
                               "the output was:\n%s" % ret.output)

    def print_help(self) -> None:
        print("%s\n"
              "=======================\n"
              "\n"
              "Using the bumpversion Versioner makes it easy to integrate more complex\n"
              "versioning into your development workflow. GoPythonGo will execute bumpversion\n"
              "for you and read the output version strings. While you can use bumpversion's\n"
              "version control integration using %s, it might not\n"
              "be a good idea to run it automatically from GoPythonGo unless you can push the\n"
              "new version upstream afterwards.\n"
              "\n"
              "You can find good information on using bumpversion here:\n"
              "  http://kylepurdon.com/blog/a-python-versioning-workflow-with-bumpversion.html\n"
              "  https://github.com/peritus/bumpversion" %
              (highlight("Bumpversion integration"), highlight("--bumpversion-opts '--commit'")))


versioner_class = BumpVersioner  # type: Type[BumpVersioner]
