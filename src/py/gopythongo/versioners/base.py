# -* encoding: utf-8 *-
from gopythongo.utils import GoPythonGoEnableSuper


class BaseVersioner(GoPythonGoEnableSuper):
    def __init__(self, *args, **kwargs):
        super(BaseVersioner, self).__init__(*args, **kwargs)

    @property
    def versioner_name(self):
        """
        Return the identifier and command-line parameter value for ==versioner used by this Versioner.
        :returns: the identifier
        :rtype: str
        """
        raise NotImplementedError("Each subclass of BaseVersioner MUST implement versioner_name")

    @property
    def can_read(self):
        raise NotImplementedError("Each subclass of BaseVersioner MUST implement can_read")

    @property
    def can_create(self):
        raise NotImplementedError("Each subclass of BaseVersioner MUST implement can_create")

    def print_help(self):
        """
        Output some information about the Versioner, like how to use it.
        """
        print("Versioner %s provides no help, unfortunately." % self.versioner_name)

    def add_args(self, parser):
        """
        Add command-line arguments to configure this Version Parser to GoPythonGo. Do NOT add *required* arguments
        to the command-line parser.

        :param parser: An ArgumentParser instance that you can call ``add_argument_group`` etc. on
        :type parser: argparse.ArgumentParser
        """
        pass

    def validate_args(self, args):
        """
        Validate the arguments added by ``add_args``. Feel free to call ``sys.exit(1)`` from here if any argument
        is invalid. Please use ``gopythongo.utils.print_error`` to output a meaningful error message to the user before
        exiting.

        :param args: The parsed command-line arguments as provided by argparse
        """
        pass

    def read(self, args):
        """
        Read a version string from wherever this Versioner reads versions. The parsed command-line arguments are
        passed along for context.
        """
        raise NotImplementedError("This Versioner does not support reading versions")

    def create(self, args):
        raise NotImplementedError("This Versioner does not support creating versions")

    def can_execute_action(self, action):
        """
        This method is called to make sure that a Versioner, given a ``VersionContainer`` instance in ``version`` can
        perform the action as defined by ``action``

        :param action: The action to be taken as set up though command-line parameters or otherwise
        :type action: str
        :returns: True or False
        """
        raise NotImplementedError("This Versioner does not support executing actions")

    @property
    def operates_on(self):
        """
        :returns: A list of strings that identify Version Parser formats that this versioner can work with in order of
                  priority/compatibility/convenience, whatever sorting criteria you choose. GoPythonGo will try to use
                  the first one, then the next, and so on.
        :rtype: List[str]
        """
        raise NotImplementedError("This Versioner does not support executing actions")

    def execute_action(self, version, action):
        """
        Execute an action on a version.

        :param version: A VersionContainter instance read by this or another Versioner
        :type version: gopythongo.versioners.parsers.VersionContainer
        :param action: The action to be taken as set up though command-line parameters or otherwise
        :type action: str
        :returns: A ``VersionContainer`` instance with the updated version (can be the same instance)
        """
        raise NotImplementedError("This Versioner does not support executing actions")

