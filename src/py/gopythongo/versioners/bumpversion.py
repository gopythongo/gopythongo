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
        gr_bv = parser.add_argument_group("Bumpversion options")
        gr_bv.add_argument("--use-bumpversion", dest="bumpversion_executable", default=None,
                           help="Set the path to the bumpversion shells script. Required if you want to use the "
                                "bumpversion Versioner.")

    def validate_args(self, args: argparse.Namespace) -> None:
        if not args.bumpversion_executable:
            raise ErrorMessage("To use the bumpversion Versioner, you must set %s" % highlight("--use-bumpversioner"))

        if not os.path.exists(args.bumpversion_executable) or not os.access(args.bumpversion_executable, os.X_OK):
            raise ErrorMessage("%s (from %s) does not exist or is not executable" %
                               (highlight(args.bumpversion_executable), highlight("--use-bumpversioner")))

    @property
    def can_read(self) -> bool:
        return True

    @property
    def can_create(self) -> bool:
        return True

    def read(self, args: argparse.Namespace) -> str:
        pass

    def create(self, args: argparse.Namespace) -> str:
        pass


versioner_class = BumpVersioner
