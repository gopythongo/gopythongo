# -* encoding: utf-8 *-

import sys
import re

from gopythongo.versioners.parsers.semverparser import SemVerVersion
from gopythongo.versioners.parsers import VersionContainer
from gopythongo.utils import print_error, highlight

versionparser_name = u"regex"


def add_args(parser):
    gr_regex = parser.add_argument_group("Regex Versioner")
    gr_regex.add_argument("--version-regex", dest="version_regex", default=None,
                          help="Select the regular expression used to parse the version string read by the version "
                               "reader. It must contain named groups for 'major', 'minor' and 'patch' and can "
                               "optionally contain named groups for 'prerelease' and 'metadata' mapping to the fields "
                               "as described by semver.org. Example: "
                               "(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<patch>[0-9]+)")


def validate_args(args):
    if args.version_parser == versionparser_name:
        if args.version_regex:
            try:
                re.compile(args.version_regex)
            except re.error as e:
                print_error("The regular expression passed to %s (%s) is invalid: %s." %
                            (highlight("--version-regex"), highlight(args.version_regex), str(e)))
                sys.exit(1)

            def check_for(str):
                if str not in args.version_regex:
                    print_error("The regular expression specified in %s must contain a named group %s." %
                                (highlight("--version-regex"), highlight(str)))

            for g in ["<major>", "<minor>", "<patch>"]:
                check_for(g)
        else:
            print_error("%s requires the parameter %s" %
                        (highlight("--version-parser=%s" % versionparser_name), highlight("--version-regex")))
            sys.exit(1)


def parse(version_str, args):
    match = re.match(args.version_regex, version_str)
    if not match:
        print_error("The regular expression '%s' does not match the version read '%s'" %
                    (highlight(args.version_regex), highlight(version_str)))
        sys.exit(1)

    def check_for(str):
        if str in match.groupdict():
            print_error("The regular expression %s does not match group %s in %s." %
                        (highlight(args.version_regex), highlight(str), version_str))
            sys.exit(1)

    for g in ["major", "minor", "patch"]:
        check_for(g)

    semver = "%s.%s.%s" % (match.group("major"), match.group("minor"), match.group("patch"))
    if "prerelease" in match.groupdict():
        semver = "%s-%s" % match.group("prerelease")
    if "metadata" in match.groupdict():
        semver = "%s+%s" % match.group("metadata")

    return VersionContainer(SemVerVersion.parse(semver), "regex")


def can_convert_from(parsername):
    """
    :returns: (bool, bool) -- a tuple saying "do I know how to convert?" and "can I do so losslessly?"
                              GoPythonGo will prefer lossless conversation and if all else is equal use the
                              target Version Parser
    """
    if parsername == versionparser_name:
        return True, True  # we can convert and we can do so losslessly
    return False, False


def can_convert_to(parsername):
    """
    :returns: (bool, bool) -- a tuple saying "do I know how to convert?" and "can I do so losslessly?"
                              GoPythonGo will prefer lossless conversation and if all else is equal use the
                              target Version Parser
    """
    if parsername == versionparser_name:
        return True, True  # we can convert and we can do so losslessly
    return False, False


def convert_from(version):
    return version


def convert_to(version, parsername):
    return version

def print_help():
    pass