# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import configargparse
import re

from typing import Any, Tuple, List, Type
from semantic_version import Version as SemVerBase

from gopythongo.utils import highlight, ErrorMessage, print_info
from gopythongo.versioners.parsers import VersionContainer, BaseVersionParser, UnconvertableVersion
from gopythongo.versioners.parsers.pep440parser import PEP440Adapter


class SemVerAdapter(SemVerBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def tostring(self) -> str:
        return str(self)


class SemVerVersionParser(BaseVersionParser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versionparser_name(self) -> str:
        return "semver"

    @property
    def supported_actions(self) -> List[str]:
        return ["bump-major", "bump-minor", "bump-patch", "bump-pre"]

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        gr_semver = parser.add_argument_group("SemVer Version Parser options")
        gr_semver.add_argument("--semver-allow-partial", dest="semver_partial", action="store_true", default=False,
                               help="Allow the parsing of incomplete version strings, which still partially comply "
                                    "with SemVer (e.g. '2.0')")
        gr_semver.add_argument("--semver-coerce", dest="semver_coerce", action="store_true", default=False,
                               help="Try really hard to make the input version into something resembling SemVer. Use "
                                    "this with caution.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        return

    def parse(self, version_str: str, args: configargparse.Namespace) -> VersionContainer[SemVerAdapter]:
        try:
            if args.semver_coerce:
                sv = SemVerAdapter.coerce(version_str, partial=args.semver_partial)
            else:
                sv = SemVerAdapter(version_str, partial=args.semver_partial)
        except ValueError as e:
            raise ErrorMessage("%s is not a valid SemVer version string (%s)" % (highlight(version_str), str(e))) from e

        return VersionContainer(sv, self.versionparser_name)

    def can_convert_from(self, parserid: str) -> Tuple[bool, bool]:
        if parserid == self.versionparser_name:
            return True, True
        elif parserid == "regex":
            return True, True
        elif parserid == "pep440":
            return True, False
        return False, False

    def can_execute_action(self, version: VersionContainer, action: str) -> bool:
        if action not in self.supported_actions:
            return False
        elif action == "bump-pre":
            for part in version.version.prerelease:
                m = re.match("(.*?)([0-9]*)(.*)", part)
                if m.group(2):
                    return True
            return False
        return True

    def execute_action(self, version: VersionContainer[SemVerAdapter], action: str) -> VersionContainer[SemVerAdapter]:
        ver = version.version
        if action == "bump-major":
            ver = ver.next_major()
        elif action == "bump-minor":
            ver = ver.next_minor()
        elif action == "bump-patch":
            ver = ver.next_patch()
        elif action == "bump-pre":
            # find something to increment
            newpre = []
            found = False
            for part in ver.prerelease:
                m = re.match("(.*?)([0-9]*)(.*)", part)
                if m.group(2):
                    # increment the first integer we find
                    newpre.append("%s%s%s" % (m.group(1), str(int(m.group(2)) + 1), m.group(3)))
                    found = True
                else:
                    newpre.append(part)

            if not found:
                raise ErrorMessage("--version-action was %s, but the prerelease part of %s does not contain an integer "
                                   "part to increment" % (highlight(action), highlight(str(ver))))

            # create a copy of the original object
            ver = SemVerAdapter(str(ver))
            ver.prerelease = tuple(newpre)
        return VersionContainer(ver, self.versionparser_name)

    @staticmethod
    def semver_from_pep440(pep440: PEP440Adapter) -> str:
        semstr = ""
        for ix in range(0, len(pep440._version.release) - 1 if len(pep440._version.release) < 3 else 2):
            semstr = "%s.%s" % (semstr, pep440._version.release[ix])
        semstr = semstr[1:]  # cut the leading dot
        if pep440.is_prerelease:
            sep = "-"  # first group gets a -, everything else a .
            if pep440._version.pre is not None:
                semstr = "%s%s%s" % (semstr, sep, "".join(str(x) for x in pep440._version.pre))
                sep = "."
            if pep440._version.dev is not None:
                semstr = "%s%s%s" % (semstr, sep, "dev{0}".format(pep440._version.dev[1]))

        # this is where we lose data, because semver doesn't know post-releases or epochs
        sep = "+"  # first metadata seperator is a +, then a .
        if pep440.is_postrelease:
            semstr = "%s%s%s" % (semstr, sep, "post{0}".format(pep440._version.post[1]))
        if pep440.local:
            semstr = "%s%s%s" % (semstr, sep, pep440.local)

        if pep440._version.epoch != 0:
            semstr = "%s%s%s" % (semstr, sep, "epoch%s" % pep440._version.epoch)

        if pep440.is_postrelease or pep440._version.epoch != 0:
            print_info("Unable to do lossless conversion to SemVer from PEP440, because SemVer does not know post-"
                       "release identifiers or epochs. (%s => %s)" % (str(pep440), semstr))
        return semstr

    def convert_from(self, version: VersionContainer[Any]) -> VersionContainer[SemVerAdapter]:
        if version.parsed_by == self.versionparser_name:
            return version
        elif version.parsed_by == "regex":
            return VersionContainer(version.version, self.versionparser_name)
        elif version.parsed_by == "pep440":
            return VersionContainer(SemVerAdapter.parse(SemVerVersionParser.semver_from_pep440(version.version)),
                                    self.versionparser_name)
        else:
            raise UnconvertableVersion("%s does not know how to convert into %s" %
                                       (self.versionparser_name, version.parsed_by))

    def deserialize(self, serialized: str) -> VersionContainer[SemVerAdapter]:
        return VersionContainer(SemVerAdapter.parse(serialized), self.versionparser_name)

    def print_help(self) -> None:
        print("%s\n"
              "=====================\n"
              "\n"
              "The %s parser parses SemVer version strings as defined by\n"
              "http://semver.org/. It does not require any additional command-line parameters,\n"
              "but it can parse *partial* SemVer strings that don't fully conform to the SemVer\n"
              "specification or even try and transform arbitrary strings. You can enable those\n"
              "features with the following command-line flags:\n"
              "\n"
              "    --semver-allow-partial    Enables partial string parsing, like '1.0'\n"
              "    --semver-coerce           Tries to convert anything you throw at it, like\n"
              "                              '1.0.whatever' to varied levels of success.\n" %
              (highlight("SemVer Version Parser"), highlight("semver")))


versionparser_class = SemVerVersionParser  # type: Type[SemVerVersionParser]
