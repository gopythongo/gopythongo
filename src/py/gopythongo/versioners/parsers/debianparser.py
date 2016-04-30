# -* encoding: utf-8 *-

import sys

from gopythongo.utils import print_error, highlight
from gopythongo.utils.debversion import DebianVersion, InvalidDebianVersionString
from gopythongo.versioners.parsers import VersionContainer

versionparser_name = u"debian"


def add_args(parser):
    pass


def validate_args(args):
    pass


def parse(version_str, args):
    try:
        dv = DebianVersion.fromstring(version_str)
    except InvalidDebianVersionString as e:
        print_error("%s is not a valid Debian version string. (%s)" % (highlight(version_str), str(e)))
        sys.exit(1)

    return VersionContainer(dv, versionparser_name)


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
