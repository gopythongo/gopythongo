# -* encoding: utf-8 *-

import six

from semantic_version import Version as SemVerBase
from gopythongo.utils import highlight, print_error
from gopythongo.versioners.parsers import VersionContainer

versionparser_name = u"semver"


class SemVerVersion(SemVerBase):
    def __init__(self, *args):
        super(SemVerVersion, self).__init__(*args)

    def tostring(self):
        return six.u(self)


def add_args(parser):
    pass


def validate_args(args):
    pass


def parse(version_str, args):
    try:
        sv = SemVerVersion.parse(version_str)
    except ValueError as e:
        print_error("%s is not a valid SemVer version string (%s)" % (highlight(version_str), str(e)))

    return VersionContainer(sv, versionparser_name)


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
