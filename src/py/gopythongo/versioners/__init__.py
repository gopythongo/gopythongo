# -* encoding: utf-8 *-

import pkg_resources
import sys

from gopythongo.utils.buildcontext import the_context
from gopythongo.versioners import aptly, pymodule, static, help, parsers
from gopythongo.utils import highlight, print_error, print_info, plugins

versioners = {
    "aptly": aptly,
    "pymodule": pymodule,
    "static": static,
}

version_parsers = {
    "stringformat": parsers.stringparser,
    "semver": parsers.semverparser,
    "debian": parsers.debianparser,
}


def add_args(parser):
    global versioners, version_parsers

    try:
        plugins.load_plugins("gopythongo.versioners", versioners, "versioner_name",
                             ["add_args", "validate_args", "print_help", "validate_param",
                              ["read", "create"]])
        plugins.load_plugins("gopythongo.versionparsers", version_parsers, "versionparser_name",
                             ["add_args", "validate_args", "print_help", "parse"])
    except ImportError as e:
        print_error(e.message)
        sys.exit(1)

    gp_version = parser.add_argument_group("Version determination")
    gp_version.add_argument("--help-versioner", choices=versioners.keys(), default=None,
                            action=help.VersionerHelpAction)
    gp_version.add_argument("--help-versionparser", choices=version_parsers.keys(), default=None,
                            action=parsers.help.VersionParserHelpAction)
    gp_version.add_argument("--read-version", dest="read_version", default=None,
                            help="Specify from where to read the base version string. See --help-versioner for "
                                 "details.")
    gp_version.add_argument("--version-parser", dest="version_parser", choices=version_parsers.keys(), default="semver",
                            help="Parse the version string read by --read-version with this parser. See "
                                 "--help-versionparser for details.")
    gp_version.add_argument("--new-version", dest="new_version", required=True,
                            help="Specify a format for the version string to be used for the output package. See "
                                 "--help-versioner for details.")
    gp_version.add_argument("--version-action", dest="version_action",
                            choices=["increment-epoch", "increment-patch", "increment-revision", "none"],
                            default="none",
                            help="Choose what to do to the version determined via --read-version to change the "
                                 "version for the output package before it is formatted according to "
                                 "--new-version.")

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

    if args.read_version:
        if ":" in args.read_version:
            read_versioner = args.read_version.split(":")[0]
            if read_versioner not in versioners.keys() or not \
                    hasattr(versioners[read_versioner], "read"):
                print_error("%s is not a valid versioner for reading versions. Valid readers are %s" %
                            (highlight(read_versioner), highlight(", ".join(
                                 [x for x in versioners.keys() if hasattr(versioners[x], "read")]
                             ))))
                sys.exit(1)

            versioners[read_versioner].validate_param(args.read_version[len(read_versioner) + 1:])
        else:
            print_error("%s needs a parameter in the form of '[versioner]:[parameters]'. See %s for more information." %
                        (highlight("--read-version"), highlight("--help-versioner")))
            sys.exit(1)

    if ":" in args.new_version:
        create_versioner = args.new_version.split(":")[0]
        if create_versioner not in versioners.keys() or not \
                hasattr(versioners[create_versioner], "create"):
            print_error("%s is not a valid versioner for creating version numbers. Valid versioners are %s" %
                        (highlight(create_versioner), highlight(", ".join(
                            [x for x in versioners.keys() if hasattr(versioners[x], "create")]
                        ))))
            sys.exit(1)

        versioners[create_versioner].validate_param(args.new_version[len(create_versioner) + 1:])
    else:
        print_error("%s needs a parameter in the form of '[versioner]:[parameters]'. See %s for more information." %
                    (highlight("--read-version"), highlight("--help-versioner")))
        sys.exit(1)


def version(args):
    reader = versioners[args.read_version.split(":")[0]]
    version_str = versioners[reader].read(args)
    print_info("Read version using versioner %s: %s" % (highlight(reader), highlight(version_str)))

    the_context.read_version = version_parsers[args.version_parser].parse(version_str)
