# -* encoding: utf-8 *-
from gopythongo.versioners.parsers import BaseVersionParser
from packaging.version import Version, parse


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

