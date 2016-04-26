# -* encoding: utf-8 *-

import pkg_resources
import sys

from gopythongo.utils.buildcontext import the_context
from gopythongo.versioners import aptly, pymodule, static, help, parsers
from gopythongo.utils import highlight, print_error, print_info

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

    # load external modules
    for entry_point in pkg_resources.iter_entry_points("gopythongo.versioners"):
        module = entry_point.load()
        if hasattr(module, "__versioner_name__"):
            if hasattr(module, "add_args") and hasattr(module, "validate_args") and \
                    hasattr(module, "print_help") and hasattr(module, "validate_param") and \
                    (hasattr(module, "read") or hasattr(module, "create")):
                versioners[module.__versioner_name__] = module
            else:
                print_error("A versioner plug-in must have at least either read() or create() implementations, "
                            "add_args(), validate_args(), validate_param() and print_help(). %s (%s) is faulty." %
                            (highlight(module.__versioner_name__), highlight(module.__name__)))
                sys.exit(1)
        else:
            print_error("A versioner plug-in must have a __versioner_name__ attribute. %s seems to have none." %
                        highlight(module.__name__))
            sys.exit(1)

    for entry_point in pkg_resources.iter_entry_points("gopythongo.versionparsers"):
        module = entry_point.load()
        if hasattr(module, "__versionparser_name__"):
            if hasattr(module, "add_args") and hasattr(module, "validate_args") and \
                    hasattr(module, "print_help") and hasattr(module, "parse"):
                version_parsers[module.__versionparser_name__] = module
            else:
                print_error("A versionparser plug-in must have implementations for add_args(), validate_args(), "
                            "print_help() and parse(). %s (%s) is faulty." %
                            (highlight(module.__versionparser_name__), highlight(module.__name__)))
        else:
            print_error("A versionparser plug-in must have a __versionparser_name__ attribute. %s seems to have none." %
                        highlight(module.__name__))
            sys.exit(1)

    gp_version = parser.add_argument_group("Version determination")
    gp_version.add_argument("--help-versioner", choices=versioners.keys(), default=None,
                            action=help.VersionerHelpAction)
    gp_version.add_argument("--help-versionparser", choices=version_parsers.keys(), default=None,
                            action=parsers.help.VersionParserHelpAction)
    gp_version.add_argument("--read-version", dest="read_version", default=None,
                            help="Specify from where to read the base version string. See --help-versioner for "
                                 "details.")
    gp_version.add_argument("--version-parser", dest="version_parser", default="semver",
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


def validate_args(args):
    for v in versioners.values():
        v.validate_args(args)

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


def parse(version_str):
    pass


def version(args):
    reader = versioners[args.read_version.split(":")[0]]
    version_str = versioners[reader].read(args)
    print_info("Read version using versioner %s: %s" % (highlight(reader), highlight(version_str)))

    the_context.read_version = parse(version_str)
