# -* encoding: utf-8 *-


class UnknownParserName(Exception):
    pass


class UnconvertableVersion(Exception):
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

        target_can_convert, target_losslessly = version_parsers[parsername].can_convert_from(self.parsed_by)
        if target_can_convert and target_losslessly:
            return version_parsers[parsername].convert_from(self.version, self.parsed_by)

        source_can_convert, source_losslessly = version_parsers[self.parsed_by].can_convert_to(parsername)
        if source_can_convert and source_losslessly:
            return version_parsers[self.parsed_by].convert_to(self.version, parsername)

        if target_can_convert:
            return version_parsers[parsername].convert_from(self.version, self.parsed_by)

        if source_can_convert:
            return version_parsers[parsername].convert_from(self.version, self.parsed_by)

        raise UnconvertableVersion("No known way to convert version data from %s to %s" % (self.parsed_by, parsername))

    def perform_action(self, action):
        from gopythongo.versioners import version_parsers
        self.version = version_parsers[self.parsed_by].perform_action(self.version, action)
