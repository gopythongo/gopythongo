# -* encoding: utf-8 *-
import argparse
import re

from typing import Any

from gopythongo.versioners.parsers.semverparser import SemVerVersion
from gopythongo.versioners.parsers import VersionContainer, BaseVersionParser
from gopythongo.utils import highlight, ErrorMessage


class RegexVersionParser(BaseVersionParser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        gr_regex = parser.add_argument_group("Regex Versioner")
        gr_regex.add_argument("--version-regex", dest="version_regex", default=None,
                              help="Select the regular expression used to parse the version string read by the version "
                                   "reader. It must contain named groups for 'major', 'minor' and 'patch' and can "
                                   "optionally contain named groups for 'prerelease' and 'metadata' mapping to the "
                                   "fields as described by semver.org. Example: "
                                   "(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<patch>[0-9]+)")

    @property
    def versionparser_name(self) -> str:
        return u"regex"

    def validate_args(self, args: argparse.Namespace) -> None:
        if args.version_parser == self.versionparser_name:
            if args.version_regex:
                try:
                    re.compile(args.version_regex)
                except re.error as e:
                    raise ErrorMessage("The regular expression passed to %s (%s) is invalid: %s." %
                                       (highlight("--version-regex"), highlight(args.version_regex), str(e)))

                def check_for(string: str) -> None:
                    if string not in args.version_regex:
                        raise ErrorMessage("The regular expression specified in %s must contain a named group %s." %
                                           (highlight("--version-regex"), highlight(string)))

                for g in ["<major>", "<minor>", "<patch>"]:
                    check_for(g)
            else:
                raise ErrorMessage("%s requires the parameter %s" %
                                   (highlight("--version-parser=%s" % self.versionparser_name),
                                    highlight("--version-regex")))

    def parse(self, version_str: str, args: argparse.Namespace) -> VersionContainer:
        match = re.match(args.version_regex, version_str)
        if not match:
            raise ErrorMessage("The regular expression '%s' does not match the version read '%s'" %
                               (highlight(args.version_regex), highlight(version_str)))

        def check_for(string: str) -> None:
            if string in match.groupdict():
                raise ErrorMessage("The regular expression %s does not match group %s in %s." %
                                   (highlight(args.version_regex), highlight(string), version_str))

        for g in ["major", "minor", "patch"]:
            check_for(g)

        semver = "%s.%s.%s" % (match.group("major"), match.group("minor"), match.group("patch"))
        if "prerelease" in match.groupdict():
            semver = "%s-%s" % match.group("prerelease")
        if "metadata" in match.groupdict():
            semver = "%s+%s" % match.group("metadata")

        return VersionContainer(SemVerVersion.parse(semver), self.versionparser_name)

    def print_help(self) -> None:
        print("%s\n"
              "=================================\n"
              "\n"
              "The %s Version Parser tries to make it easy to convert arbitrary version\n"
              "strings into SemVer-compatible versions. It does this by requiring an\n"
              "additional command-line parameter --version-regex which takes a regular\n"
              "expression as its argument. That regular expression must contain named groups\n"
              "with the following names: %s, %s, %s and optionally %s and\n"
              "%s. A full regular expression parsing a valid SemVer-compatible string\n"
              "would therefor be:\n"
              "\n"
              "    '(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<patch>[0-9]+)' +\n"
              "    '-(?P<prerelease>.*?)\+(?P<metadata>.*)'\n"
              "\n"
              "You should use this parser to make it easy to read arbitrary version strings\n"
              "that don't fit any of the other supported formats.\n" %
              (highlight("Regular Expression Version Parser"), highlight("regex"),
               highlight("major"), highlight("minor"), highlight("patch"),
               highlight("prerelease"), highlight("metadata")))


versionparser_class = RegexVersionParser
