# -* encoding: utf-8 *-

import sys

from gopythongo.utils.buildcontext import the_context
from gopythongo.versioners import aptly, pymodule, static, help as versioner_help
from gopythongo.utils import highlight, print_error, print_info, plugins, GoPythonGoEnableSuper
from gopythongo.versioners.parsers import regexparser, semverparser, debianparser, help as parser_help, \
    BaseVersionParser

versioners = {
    u"aptly": aptly,
    u"pymodule": pymodule.PymoduleVersioner(),
    u"static": static,
}

version_parsers = {
    u"regex": regexparser.RegexVersionParser(),
    u"semver": semverparser.SemVerVersionParser(),
    u"debian": debianparser.DebianVersionParser(),
}


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

    def print_help(self):
        """
        Output some information about the Versioner, like how to use it.
        """
        print("Versioner %s provides no help, unfortunately." % self.versioner_name)

    def add_args(self, parser):
        """
        Add command-line arguments to configure this Version Parser to GoPythonGo.

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

    def read(self, readspec):
        raise NotImplementedError("Each subclass of BaseVersioner MUST implement read()")


def add_args(parser):
    global versioners, version_parsers

    try:
        plugins.load_plugins("gopythongo.versioners", versioners, "versioner_class", BaseVersioner,
                             "versioner_name")
        plugins.load_plugins("gopythongo.versionparsers", version_parsers, "versionparser_class",
                             BaseVersionParser, "versionparser_name")
    except ImportError as e:
        print_error(str(e))
        sys.exit(1)

    gp_version = parser.add_argument_group("Version determination")
    gp_version.add_argument("--help-versioner", choices=versioners.keys(), default=None,
                            action=versioner_help.VersionerHelpAction)
    gp_version.add_argument("--help-versionparser", choices=version_parsers.keys(), default=None,
                            action=parser_help.VersionParserHelpAction)
    gp_version.add_argument("--versioner", dest="versioner", default=None,
                            help="Specify from where to read the base version string. See --help-versioner for "
                                 "details. Most versioners have specific additional command-line parameters.")
    gp_version.add_argument("--version-parser", dest="version_parser", choices=version_parsers.keys(), default="semver",
                            help="Parse the version string read by --versioner with this parser. See "
                                 "--help-versionparser for details.")
    gp_version.add_argument("--new-version", dest="version_creator", required=True,
                            help="Specify the version format into which the version should be converted (can be the "
                                 "same) before applying the selected version action to create the final version string "
                                 "to be used for the output package. See --help-versionparser for details.")
    gp_version.add_argument("--version-action", dest="version_action",
                            choices=["increment-epoch", "increment-patch", "increment-revision", "none"],
                            default="none",
                            help="Choose what to do to the version for the output package after it is "
                                 "formatted/converted according to --new-version.")

    for v in versioners.values():
        v.add_args(parser)

    for vp in version_parsers.values():
        vp.add_args(parser)


def validate_args(args):
    for v in versioners.values():
        v.validate_args(args)

    for vp in version_parsers.values():
        vp.validate_args(args)

    if args.version_parser not in version_parsers:
        print_error("%s is not a valid version parser. Valid options are: %s" %
                    (highlight(args.version_parser), ", ".join(version_parsers.keys())))
        sys.exit(1)

    if args.versioner:
        if args.versioner not in versioners.keys():
            print_error("%s is not a valid versioner for reading versions. Valid readers are %s" %
                        (highlight(args.versioner), highlight(", ".join(
                             [x for x in versioners.keys() if hasattr(versioners[x], "read")]
                         ))))
            sys.exit(1)

        versioners[read_versioner].validate_param(args.read_version[len(read_versioner) + 1:])

    if args.version_creator not in version_parsers:
        print_error("%s is not a valid version formatter/parser for creating version numbers. Valid options are %s" %
                    (highlight(args.version_creator), ", ".join(version_parsers.keys())))
        sys.exit(1)


def version(args):
    reader_name = args.read_version.split(":")[0]
    param = args.read_version[len(reader_name) + 1:]

    reader = versioners[reader_name]
    version_str = reader.read(param)
    print_info("Read version using versioner %s: %s" % (highlight(reader_name), highlight(version_str)))

    the_context.read_version = version_parsers[args.version_parser].parse(version_str, args)
