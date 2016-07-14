# -* encoding: utf-8 *-
import argparse
import re

from typing import Any, Tuple, List

from gopythongo.utils import highlight, ErrorMessage
from gopythongo.utils.debversion import DebianVersion, InvalidDebianVersionString
from gopythongo.versioners.parsers import VersionContainer, BaseVersionParser
from gopythongo.versioners.parsers.pep440parser import PEP440Adapter


class DebianVersionParser(BaseVersionParser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versionparser_name(self) -> str:
        return "debian"

    @property
    def supported_actions(self) -> List[str]:
        return ["bump-epoch", "bump-revision"]

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        pass

    def validate_args(self, args: argparse.Namespace) -> None:
        if args.version_action not in self.supported_actions:
            raise ErrorMessage("Debian Version Parser does not support the selected action (%s). Supported version "
                               "actions are: %s" % (highlight(args.version_action), ", ".join(self.supported_actions)))

    def parse(self, version_str: str, args: argparse.Namespace) -> VersionContainer[DebianVersion]:
        try:
            dv = DebianVersion.fromstring(version_str)
        except InvalidDebianVersionString as e:
            raise ErrorMessage("%s is not a valid Debian version string: %s" % (highlight(version_str), str(e))) from e

        return VersionContainer(dv, self.versionparser_name)

    def can_execute_action(self, version: VersionContainer, action: str) -> bool:
        if action in self.supported_actions:
            return True

    def execute_action(self, version: VersionContainer[DebianVersion], action: str) -> VersionContainer[DebianVersion]:
        # make a copy of the DebianVersion object
        ver = DebianVersion.fromstring(version.version.tostring())
        if action == "bump-epoch":
            if ver.epoch:
                ver.epoch = str(int(ver.epoch) + 1)
            else:
                ver.epoch = "1"
        elif action == "bump-revision":
            # find the first number group in revision and increment it
            if ver.revision:
                matches = re.search("([0-9]+)", ver.revision)
                if matches:
                    # replace the first occurrence
                    ver.revision.replace(matches.group(1), str(int(matches.group(1)) + 1), 1)
                else:
                    raise ErrorMessage("Version Action is '%s', but the revision string of %s (revision=%s) does not "
                                       "contain an incrementable integer number" %
                                       (highlight(action), highlight(str(ver)), highlight(ver.revision)))
            else:
                ver.revision = "1"
        return VersionContainer(ver, self.versionparser_name)

    def deserialize(self, serialized: str) -> VersionContainer:
        return VersionContainer(DebianVersion.fromstring(serialized), self.versionparser_name)

    def can_convert_from(self, parserid: str) -> Tuple[bool, bool]:
        if parserid == self.versionparser_name:
            return True, True  # we can convert and we can do so losslessly
        elif parserid == "semver":
            return True, True  # all of semver can be encoded in the Debian standard
        elif parserid == "pep440":
            return True, True  # all of pep440 can be encoded in the Debian standard
        elif parserid == "regex":
            return True, True  # regex really uses semver under the hood, so it's the same
        return False, False

    def convert_from(self, version: VersionContainer[Any]) -> VersionContainer[DebianVersion]:
        if version.parsed_by == self.versionparser_name:
            return version
        elif version.parsed_by in ["semver", "regex"]:
            sv = str(version.version)
            if version.version.prerelease:
                # translate a semver prelease to a Debian prerelease marker
                sv = sv.replace("-", "~", 1)
            return VersionContainer(DebianVersion.fromstring(sv), self.versionparser_name)
        elif version.parsed_by == "pep440":
            pva = version.version  # type: PEP440Adapter

            # translate pep440 "-pre/rc/a" prerelease marker to Debian prerelease (~)
            verstr = "".join(pva.to_parts(pre_prefix="~", dev_prefix="~"))
            if "!" in verstr:
                verstr = verstr.split("!", 1)[1]  # remove the epoch, we'll add it later in the constructor

            try:
                dv = DebianVersion(pva._version.epoch if pva._version.epoch != 0 else None, verstr, None)
            except InvalidDebianVersionString as e:
                raise ErrorMessage("Unable to convert PEP440 version string to valid Debian version string: %s" %
                                   highlight(str(pva))) from e
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
