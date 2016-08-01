# -* encoding: utf-8 *-
import configargparse

from typing import Any, Type

from gopythongo.utils import highlight, ErrorMessage
from gopythongo.versioners import BaseVersioner


class StaticVersioner(BaseVersioner):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versioner_name(self) -> str:
        return u"static"

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        gp_static = parser.add_argument_group("Static Versioner options")
        gp_static.add_argument("--static-version", dest="static_version", default=None,
                               help="The static version string to use.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        if not args.static_version:
            raise ErrorMessage("Static versioner requires %s" % highlight("--static-version"))

    @property
    def can_read(self) -> bool:
        return True

    def read(self, args: configargparse.Namespace) -> str:
        return args.static_version

    def print_help(self) -> None:
        print("Static Versioner\n"
              "================\n"
              "\n"
              "The static Versioner simply reads a version string from the command-line\n"
              "parameter %s.\n" % highlight("--static-version"))


versioner_class = StaticVersioner  # type: Type[StaticVersioner]
