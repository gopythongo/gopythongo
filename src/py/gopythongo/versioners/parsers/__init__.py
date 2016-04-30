# -* encoding: utf-8 *-


class UnknownParserName(Exception):
    pass


class VersionContainer(object):
    def __init__(self, version, parsed_by):
        self.version = version
        self.parsed_by = parsed_by

    def convert_to(self, parsername):
        from gopythongo.versioners import version_parsers
        if parsername not in version_parsers:
            raise UnknownParserName("Unknown parser name: %s" % parsername)

        if parsername == self.parsed_by:
            return self

        if version_parsers[parsername].can_losslessly_convert_from(self.parsed_by):
            return version_parsers[parsername].convert_from(self.version, self.parsed_by)
        else:
            return version_parsers[self.parsed_by].convert_to(self.version, parsername)

    def perform_action(self, action):
        from gopythongo.versioners import version_parsers
        self.version = version_parsers[self.parsed_by].perform_action(self.version, action)
