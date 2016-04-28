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


def print_help():
    pass
