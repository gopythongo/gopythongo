# -* encoding: utf-8 *-
import argparse

from typing import Any

from gopythongo.utils import highlight, ErrorMessage
from gopythongo.versioners.parsers import BaseVersionParser, VersionContainer
from packaging.version import parse, InvalidVersion


class PEP440VersionParser(BaseVersionParser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versionparser_name(self) -> str:
        return u"pep440"

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        pass

    def validate_args(self, args: argparse.Namespace) -> None:
        pass

    def parse(self, version_str: str, args: argparse.Namespace) -> VersionContainer:
        try:
            version = parse(version_str)
        except InvalidVersion as e:
            raise ErrorMessage("%s is not a valid PEP-440 version string: %s" %
                               (highlight(version_str), str(e))) from e

        return VersionContainer(version, self.versionparser_name)

    def print_help(self) -> None:
        print("%s\n"
              "=====================\n"
              "\n"
              "The %s Version Parser should be used with PIP/PEP-440 version strings.\n"
              "This is by far the easiest choice if you're uploading your source code to the\n"
              "cheeseshop (pypi) or a local pypi installation through setup.py anyway, since\n"
              "that means that the version string used by your setup.py is probably already\n"
              "pep440-compatible anyway.\n"
              "\n"
              "The PEP440 Version Parser does not require any additional configuration.\n" %
              (highlight("PEP440 Version Parser"), highlight("pep440")))


versionparser_class = PEP440VersionParser
