# -* encoding: utf-8 *-

import sys

from gopythongo.utils.buildcontext import the_context
from gopythongo.versioners import aptly, pymodule, static, help as versioner_help
from gopythongo.utils import highlight, print_error, print_info, plugins
from gopythongo.versioners.parsers import regexparser, semverparser, debianparser, help as parser_help, \
    BaseVersionParser

versioners = {
    u"aptly": aptly.AptlyVersioner(),
    u"pymodule": pymodule.PymoduleVersioner(),
    u"static": static.StaticVersioner(),
}

version_parsers = {
    u"regex": regexparser.RegexVersionParser(),
    u"semver": semverparser.SemVerVersionParser(),
    u"debian": debianparser.DebianVersionParser(),
}


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
    gp_version.add_argument("--input-versioner", dest="input_versioner", default=None,
                            help="Specify from where to read the base version string. See --help-versioner for "
                                 "details. Most versioners have specific additional command-line parameters.")
    gp_version.add_argument("--version-parser", dest="version_parser", choices=version_parsers.keys(), default="semver",
                            help="Parse the version string read by --versioner with this parser. See "
                                 "--help-versionparser for details.")
    gp_version.add_argument("--output-versioner", dest="output_versioner", required=True,
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
    if args.version_parser not in version_parsers:
        print_error("%s is not a valid version parser. Valid options are: %s" %
                    (highlight(args.version_parser), ", ".join(version_parsers.keys())))
        sys.exit(1)

    if args.input_versioner:
        if args.input_versioner in versioners.keys():
            versioners[args.input_versioner].validate_args(args)
        else:
            print_error("%s is not a valid versioner for reading versions. Valid options are %s" %
                        (highlight(args.versioner), highlight(", ".join(
                            [x for x in versioners.keys() if versioners[x].can_read]
                        ))))
            sys.exit(1)

    if args.version_parser in version_parsers:
        version_parsers[args.version_parser].validate_args(args)
    else:
        print_error("%s is not a valid Version Parser for parsing version numbers. Valid options are %s" %
                    (highlight(args.version_parser), ", ".join(version_parsers.keys())))
        sys.exit(1)

    if args.output_versioner:
        if args.output_versioner not in versioners.keys():
            versioners[args.output_versioner].validate_args(args)
        else:
            print_error("%s is not a valid versioner for creating/modifying versions. Valid options are %s" %
                        (highlight(args.versioner), highlight(", ".join(
                            [x for x in versioners.keys() if versioners[x].can_write]
                        ))))
            sys.exit(1)


def version(args):
    reader_name = args.read_version.split(":")[0]
    param = args.read_version[len(reader_name) + 1:]

    reader = versioners[reader_name]
    version_str = reader.read(param)
    print_info("Read version using versioner %s: %s" % (highlight(reader_name), highlight(version_str)))

    the_context.read_version = version_parsers[args.version_parser].parse(version_str, args)
