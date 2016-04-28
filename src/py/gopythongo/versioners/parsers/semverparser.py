# -* encoding: utf-8 *-

import six

from semantic_version import Version as SemVerBase


versionparser_name = u"semver"


class SemVerVersion(SemVerBase):
    def __init__(self, *args):
        super(SemVerVersion, self).__init__(*args)

    def tostring(self):
        return six.u(self)


def add_args(parser):
    pass


def validate_args(parser):
    pass


def parse(version_str):
    pass
