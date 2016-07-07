# -* encoding: utf-8 *-
import argparse
import sys
from typing import List, Dict, Type, Any

from gopythongo.utils import highlight, print_info, plugins, CommandLinePlugin, ErrorMessage
from gopythongo.versioners.parsers import help as parser_help, BaseVersionParser, VersionContainer
from gopythongo.versioners import help as versioner_help


versioners = {}  # type: Dict[str, 'BaseVersioner']
version_parsers = {}  # type: Dict[str, BaseVersionParser]


def init_subsystem() -> None:
    global versioners, version_parsers
    from gopythongo.versioners import aptly, pymodule, bumpversion, static
    from gopythongo.versioners.parsers import regexparser, semverparser, debianparser, pep440parser

    versioners = {
        u"aptly": aptly.versioner_class(),
        u"pymodule": pymodule.versioner_class(),
        u"bumpversion": bumpversion.versioner_class(),
        u"static": static.versioner_class(),
    }

    version_parsers = {
        u"regex": regexparser.versionparser_class(),
        u"semver": semverparser.versionparser_class(),
        u"debian": debianparser.versionparser_class(),
        u"pep440": pep440parser.versionparser_class(),
    }

    plugins.load_plugins("gopythongo.versioners", versioners, "versioner_class", BaseVersioner,
                         "versioner_name")
    plugins.load_plugins("gopythongo.versionparsers", version_parsers, "versionparser_class",
                         BaseVersionParser, "versionparser_name")


class BaseVersioner(CommandLinePlugin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versioner_name(self) -> str:
        """
        **@property**

        Return the identifier and command-line parameter value for ==versioner used by this Versioner.
        :returns: the identifier
        :rtype: str
        """
        raise NotImplementedError("Each subclass of BaseVersioner MUST implement versioner_name")

    @property
    def can_read(self) -> bool:
        """
        **@property**
        """
        raise NotImplementedError("Each subclass of BaseVersioner MUST implement can_read")

    def print_help(self) -> None:
        """
        Output some information about the Versioner, like how to use it.
        """
        print("Versioner %s provides no help, unfortunately." % self.versioner_name)

    def read(self, args: argparse.Namespace) -> str:
        """
        Read a version string from wherever this Versioner reads versions. The parsed command-line arguments are
        passed along for context.
        """
        raise NotImplementedError("This Versioner does not support reading versions")


def add_args(parser: argparse.ArgumentParser) -> None:
    global versioners, version_parsers

    collected_actions = set()
    collected_actions.add("none")
    for vp in version_parsers.values():
        for action in vp.supported_actions:
            collected_actions.add(action)

    gp_version = parser.add_argument_group("Version determination")
    gp_version.add_argument("--help-versioner", choices=versioners.keys(), default=None,
                            action=versioner_help.VersionerHelpAction)
    gp_version.add_argument("--help-versionparser", choices=version_parsers.keys(), default=None,
                            action=parser_help.VersionParserHelpAction)
    gp_version.add_argument("--versioner", dest="input_versioner", default=None,
                            help="Specify from where to read the base version string. See --help-versioner for "
                                 "details. Most versioners take specific additional command-line parameters")
    gp_version.add_argument("--version-parser", dest="version_parser", choices=version_parsers.keys(), default="semver",
                            help="Parse the version string read by --versioner with this parser. See "
                                 "--help-versionparser for details")
    gp_version.add_argument("--version-action", dest="version_action",
                            choices=collected_actions, default="none",
                            help="Choose what to do to the version for the output package. Most included Version "
                                 "Parsers can only increment numeric version parts. If you need more control, you "
                                 "should take a look at the bumpversion Versioner")

    for v in versioners.values():
        v.add_args(parser)

    for vp in version_parsers.values():
        vp.add_args(parser)


def validate_args(args: argparse.Namespace) -> None:
    if args.version_parser not in version_parsers:
        raise ErrorMessage("%s is not a valid version parser. Valid options are: %s" %
                           (highlight(args.version_parser), ", ".join(version_parsers.keys())))

    if args.input_versioner:
        if args.input_versioner in versioners.keys():
            versioners[args.input_versioner].validate_args(args)
        else:
            raise ErrorMessage("%s is not a valid versioner for reading versions. Valid options are %s" %
                               (highlight(args.versioner), highlight(", ".join(
                                   [x for x in versioners.keys() if versioners[x].can_read]
                               ))))

    if args.version_parser in version_parsers:
        version_parsers[args.version_parser].validate_args(args)
    else:
        raise ErrorMessage("%s is not a valid Version Parser for parsing version numbers. Valid options are %s" %
                           (highlight(args.version_parser), ", ".join(version_parsers.keys())))


def version(args: argparse.Namespace) -> None:
    reader_name = args.input_versioner
    reader = versioners[reader_name]
    version_str = None
    if not args.is_inner:
        version_str = reader.read(args)
        print_info("Read version using versioner %s: %s" % (highlight(reader_name), highlight(version_str)))

    from gopythongo.utils.buildcontext import the_context
    if args.is_inner:
        the_context.read_version = version_parsers[args.version_parser].deserialize(args.inner_vin)
        the_context.out_version = version_parsers[args.version_parser].deserialize(args.inner_vout)
    else:
        the_context.read_version = version_parsers[args.version_parser].parse(version_str, args)
        # TODO: execute action
