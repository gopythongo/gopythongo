# -* encoding: utf-8 *-

from . import debianparser, help, regexparser, semverparser


class VersionContainer(object):
    def __init__(self, version, parsed_by):
        self.version = version
        self.parsed_by = parsed_by
