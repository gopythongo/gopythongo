# -* encoding: utf-8 *-
import argparse

from typing import Any

from gopythongo.utils import highlight, ErrorMessage
from gopythongo.utils.debversion import DebianVersion, InvalidDebianVersionString
from gopythongo.versioners.parsers import VersionContainer, BaseVersionParser


class DebianVersionParser(BaseVersionParser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versionparser_name(self) -> str:
        return u"debian"

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        pass

    def parse(self, version_str: str, args: argparse.Namespace) -> VersionContainer:
        try:
            dv = DebianVersion.fromstring(version_str)
        except InvalidDebianVersionString as e:
            raise ErrorMessage("%s is not a valid Debian version string: %s" % (highlight(version_str), str(e))) from e

        return VersionContainer(dv, self.versionparser_name)

    def print_help(self) -> None:
        print("%s\n"
              "=====================\n"
              "\n"
              "The %s version parser works with version strings in the format specified by\n"
              "the Debian Policy Manual in \n"
              "\n"
              "    https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version\n"
              "\n"
              "It's the right choice if you specify your version strings in a format that is\n"
              "incompatible with PEP-440 or SemVer, since it's much more permissive. Most\n"
              "other version string formats can be easily transformed into Debian version\n"
              "strings.\n"
              "\n"
              "The Debian Version Parser does not require any additional configuration.\n" %
              (highlight("Debian Version Parser"), highlight("debian")))


versionparser_class = DebianVersionParser
