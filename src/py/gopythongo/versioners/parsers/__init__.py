# -* encoding: utf-8 *-

from gopythongo.utils import CommandLinePlugin


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


class BaseVersionParser(CommandLinePlugin):
    """
    A base class for Version Parsers for GoPythonGo. You can register your own Version Parsers by using setuptools
    pkg_resources entry_points. Like this: ::

        # setup.py
        ...
        setup(
            ...,
            entry_points={
                'gopythongo.versionparser': ['boink = boinkmodule',]
            },
        )

    GoPythonGo will look for an attribute called ``versionparser_class`` on ``boinkmodule`` which must point to a
    subclass of ``BaseVersionParser``. This parser will be registered under the identifier returned by the
    ``versionparser_name`` property of the subclass.
    """
    def __init__(self, *args, **kwargs):
        super(BaseVersionParser, self).__init__(*args, **kwargs)

    @property
    def versionparser_name(self):
        """
        Return the identifier and command-line parameter value for ==version-parser used by this Version Parser.
        :returns: the identifier
        :rtype: str
        """
        raise NotImplementedError("Each subclass of BaseVersionParser MUST implement versionparser_name")

    def print_help(self):
        """
        Output some information about the Version Parser, like how to use it, what it's format looks like, things like
        that. Then exit.
        """
        print("Version Parser %s provides no help, unfortunately." % self.versionparser_name)

    def parse(self, version_str, args):
        """
        Is called by GoPythonGo to parse a version string as it was read by a Versioner.

        :param version_str: The version string read by the Versioner
        :type version_str: str
        :param args: The parsed command-line arguments as provided by argparse
        """
        raise NotImplementedError("Every Version Parser MUST implement parse()")

    def can_convert_from(self, parserid):
        """
        Is called by GoPythonGo to query whether this Version Parser can read version strings from a certain format.
        You should be familiar with the code of the other parser to write this.

        :type parserid: str
        :returns: a tuple saying "do I know how to convert?" and "can I do so losslessly?". GPythonGo will prefer
                  lossless conversion and if all else is equal use the target Version Parser
        :rtype: (bool, bool)
        """
        if parserid == self.versionparser_name:
            return True, True  # we can convert and we can do so losslessly
        return False, False

    def can_convert_to(self, parserid):
        """
        Is called by GoPythonGo to query whether this Version Parser can create version strings in a certain format.
        You should be familiar with the code of the other parser to write this.

        :type parserid: str
        :returns: a tuple saying "do I know how to convert?" and "can I do so losslessly?". GoPythonGo will prefer
                  lossless conversion and if all else is equal use the target Version Parser
        :rtype: (bool, bool)
        """
        if parserid == self.versionparser_name:
            return True, True  # we can convert and we can do so losslessly
        return False, False

    def convert_from(self, version):
        """
        :type version: VersionContainer
        """
        if version.parsed_by == self.versionparser_name:
            return version
        raise UnconvertableVersion("%s does not know how to convert versions read by %s" %
                                   (self.versionparser_name, version.parsed_by))

    def convert_to(self, version, parserid):
        """
        :type version: VersionContainer
        :type parserid: str
        """
        if version.parsed_by == self.versionparser_name:
            return version
        else:
            raise UnconvertableVersion("%s does not know how to convert into %s" %
                                       (self.versionparser_name, parserid))
