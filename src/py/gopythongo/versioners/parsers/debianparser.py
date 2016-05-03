# -* encoding: utf-8 *-

import sys

from gopythongo.utils import print_error, highlight
from gopythongo.utils.debversion import DebianVersion, InvalidDebianVersionString
from gopythongo.versioners.parsers import VersionContainer, BaseVersionParser


class DebianVersionParser(BaseVersionParser):
    def __init__(self, *args, **kwargs):
        super(DebianVersionParser, self).__init__(*args, **kwargs)

    @property
    def versionparser_name(self):
        return u"debian"

    def add_args(self, parser):
        pass

    def parse(self, version_str, args):
        try:
            dv = DebianVersion.fromstring(version_str)
        except InvalidDebianVersionString as e:
            print_error("%s is not a valid Debian version string. (%s)" % (highlight(version_str), str(e)))
            sys.exit(1)

        return VersionContainer(dv, self.versionparser_name)

    def print_help(self):
        pass


versionparser_class = DebianVersionParser
