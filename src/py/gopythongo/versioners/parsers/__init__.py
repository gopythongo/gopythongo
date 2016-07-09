# -* encoding: utf-8 *-
import argparse

from typing import Tuple, Any, List, Dict

from gopythongo.utils import CommandLinePlugin, GoPythonGoEnableSuper, ErrorMessage, highlight


def get_version_parsers() -> Dict[str, 'BaseVersionParser']:
    from gopythongo.versioners import get_version_parsers as gvp
    return gvp()


class UnknownParserName(Exception):
    pass


class UnconvertableVersion(Exception):
    pass


class VersionContainer(GoPythonGoEnableSuper):
    def __init__(self, version: Any, parsed_by: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(version, parsed_by, *args, **kwargs)
        self.version = version  # type: Any
        self.parsed_by = parsed_by  # type: str

    def convert_to(self, parsername: str) -> 'VersionContainer':
        version_parsers = get_version_parsers()
        if parsername not in version_parsers:
            raise UnknownParserName("Unknown parser name: %s" % parsername)

        if parsername == self.parsed_by:
            return self

        target_can_convert, target_losslessly = version_parsers[parsername].can_convert_from(self.parsed_by)
        if target_can_convert and target_losslessly:
            return version_parsers[parsername].convert_from(self)

        source_can_convert, source_losslessly = version_parsers[self.parsed_by].can_convert_to(parsername)
        if source_can_convert and source_losslessly:
            return version_parsers[self.parsed_by].convert_to(self, parsername)

        if target_can_convert:
            return version_parsers[parsername].convert_from(self)

        if source_can_convert:
            return version_parsers[parsername].convert_from(self)

        raise UnconvertableVersion("No known way to convert version data from %s to %s" % (self.parsed_by, parsername))

    def todict(self) -> Dict[str, str]:
        """
        returns a string representation (json) of this VersionContainer
        :param version: the version to serialize
        :return: a lossless string representation of the version information
        """
        return {
            "v": str(self.version),
            "p": self.parsed_by,
        }

    @staticmethod
    def fromdict(rep: Dict[str, str]) -> 'VersionContainer':
        """
        reads a serialized version string and puts it back into a VersionContainer
        :param serialized: the serialized version string as created by ``serialize()``
        :return: a VersionContainer instance containing the deserialized version object
        """
        version_parsers = get_version_parsers()
        if rep["p"] not in version_parsers:
            raise ErrorMessage("Tried to deserialize a version string that was created by a Version Parser which the "
                               "running version of GoPythonGo does not support. Does the version inside the build "
                               "environment differ from the outside version? The serialized string was: %s, the parser "
                               "id is %s" % (highlight(str(rep)), highlight(rep["p"])))
        return version_parsers[rep["p"]].deserialize(rep["v"])

    def __str__(self) -> str:
        return "VersionContainer(%s, %s)" % (str(self.version), self.parsed_by)


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
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versionparser_name(self) -> str:
        """
        **@property**

        Return the identifier and command-line parameter value for ==version-parser used by this Version Parser.
        :returns: the identifier
        :rtype: str
        """
        raise NotImplementedError("Each subclass of BaseVersionParser MUST implement versionparser_name")

    def print_help(self) -> None:
        """
        Output some information about the Version Parser, like how to use it, what it's format looks like, things like
        that. Then exit.
        """
        print("Version Parser %s provides no help, unfortunately." % self.versionparser_name)

    def parse(self, version_str: str, args: argparse.Namespace) -> VersionContainer:
        """
        Is called by GoPythonGo to parse a version string as it was read by a Versioner.

        :param version_str: The version string read by the Versioner
        :type version_str: str
        :param args: The parsed command-line arguments as provided by argparse
        """
        raise NotImplementedError("Every Version Parser MUST implement parse()")

    def deserialize(self, version_str: str) -> VersionContainer:
        """
        parses a version string back into a container, it should be assumed that ``version_str`` has been created by
        the parser itself so unlike ``parse()`` this should not rely on command-line arguments.
        :param version_str: the version string extracted from a previous container
        :return: A VersionContainer containing ``version_str``
        """
        raise NotImplementedError("Every Version Parser MUST implement deserialize()")

    def can_convert_from(self, parserid: str) -> Tuple[bool, bool]:
        """
        Is called by GoPythonGo to query whether this Version Parser can read version strings from a certain format.
        You should be familiar with the code of the other parser to write this.

        :type parserid: str
        :returns: a tuple saying "do I know how to convert?" and "can I do so losslessly?". GPythonGo will
                  prefer lossless conversion and if all else is equal use the target Version Parser
        :rtype: (bool, bool)
        """
        if parserid == self.versionparser_name:
            return True, True  # we can convert and we can do so losslessly
        return None

    def can_convert_to(self, parserid: str) -> Tuple[bool, bool]:
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

    def convert_from(self, version: VersionContainer) -> VersionContainer:
        """
        Convert from the input ``version`` to this parser's version format. Raise ``UnconvertableVersion`` if the
        conversion is not possible.
        :type version: VersionContainer
        :raises UnconvertableVersion: if the conversion is impossible
        """
        if version.parsed_by == self.versionparser_name:
            return version
        raise UnconvertableVersion("%s does not know how to convert versions read by %s" %
                                   (self.versionparser_name, version.parsed_by))

    def convert_to(self, version: VersionContainer, parserid: str) -> VersionContainer:
        """
        Convert from this parser's version format to the target parser's format. This requires intimate knowledge
        of the other parser's version format. Raise ``UnconvertableVersion`` if the conversion is not possible.
        :type version: VersionContainer
        :type parserid: str
        :raises UnconvertableVersion: if the conversion is impossible
        """
        if version.parsed_by == self.versionparser_name:
            return version
        else:
            raise UnconvertableVersion("%s does not know how to convert into %s" %
                                       (self.versionparser_name, parserid))

    @property
    def supported_actions(self) -> List[str]:
        """
        **@property**

        returns a list of supported actions that this Version Parser can execute on versions
        :return: a list of supported actions
        """
        return []

    def can_execute_action(self, version: VersionContainer, action: str) -> bool:
        """
        This method is called to make sure that a Version Parser, given a ``VersionContainer`` instance in ``version``
        can perform the action as defined by ``action`` on the version contained in the VersionContainer.

        :param version: The version to modify
        :type version: gopythongo.versioners.parsers.VersionContainer
        :param action: The action to be taken as set up though command-line parameters or otherwise
        :type action: str
        :returns: True or False
        """
        raise NotImplementedError("This Version Parser does not support executing actions")

    def execute_action(self, version: VersionContainer, action: str) -> VersionContainer:
        """
        Execute an action on a version.

        :param version: A VersionContainer instance read by this or another Version Parser
        :type version: gopythongo.versioners.parsers.VersionContainer
        :param action: The action to be taken as set up though command-line parameters or otherwise
        :type action: str
        :returns: A ``VersionContainer`` instance with the updated version (**must** not be the same instance)
        """
        raise NotImplementedError("This Version Parser does not support executing actions")
