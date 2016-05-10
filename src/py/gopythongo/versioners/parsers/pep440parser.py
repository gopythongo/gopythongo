# -* encoding: utf-8 *-
import sys

from gopythongo.utils import print_error, highlight
from gopythongo.versioners.parsers import BaseVersionParser, VersionContainer
from packaging.version import Version, parse, InvalidVersion


class PEP440VersionParser(BaseVersionParser):
    def __init__(self, *args, **kwargs):
        super(PEP440VersionParser, self).__init__(*args, **kwargs)

    @property
    def versionparser_name(self):
        return u"pep440"

    def add_args(self, parser):
        pass

    def validate_args(self, args):
        pass

    def parse(self, version_str, args):
        try:
            version = parse(version_str)
        except InvalidVersion as e:
            print_error("%s is not a valid PEP-440 version string: %s" %
                        (highlight(version_str), str(e)))
            sys.exit(1)

        return VersionContainer(version, self.versionparser_name)


versionparser_class = PEP440VersionParser
