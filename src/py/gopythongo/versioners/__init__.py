# -* encoding: utf-8 *-

import sys

from gopythongo.versioners import aptly, pymodule, help
from gopythongo.utils import highlight, print_error


versioners = {
    "aptly": aptly,
    "pymodule": pymodule,
}


def add_args(parser):
    gp_version = parser.add_argument_group("Version determination")
    gp_version.add_argument("--help-versioner", choices=versioners.keys(), default=None,
                            action=help.VersionerHelpAction)
    gp_version.add_argument("--read-version", dest="read_version", default=None,
                            help="Specify from where to read the base version string. See --help-versioner for "
                                 "details.")
    gp_version.add_argument("--parse-version-format", dest="parse_version", default=None,
                            help="Parse the version string read by --read-version in a specific way.")
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
    if args.read_version:
        if ":" in args.read_version:
            if args.read_version.split(":")[0] in versioners.keys():
                if not hasattr(versioners[args.read_version.split(":")[0]], "read"):
                    print_error("%s is not a valid versioner for reading versions. Valid readers are %s" %
                                (highlight(args.read_version.split(":")[0]),
                                 highlight(", ".join(
                                     [x for x in versioners.keys() if hasattr(versioners[x], "read")]
                                 ))))
                    sys.exit(1)
            else:
                print_error("%s is not a valid versioner for reading versions. Valid readers are %s" %
                            (highlight(args.read_version.split(":")[0]), highlight(", ".join(
                                [x for x in versioners.keys() if hasattr(versioners[x], "read")]
                            ))))
                sys.exit(1)

        else:
            print_error("%s needs a parameter in the form of '[versioner]:[parameters]'. See %s for more information." %
                        (highlight("--read-version"), highlight("--help-versioner")))
            sys.exit(1)

    if ":" in args.new_version:
        if args.new_version.split(":")[0] not in versioners.keys():
            print_error("%s is not a valid versioner for creating version numbers. Valid versioners are %s" %
                        (highlight(args.new_version.split(":"[0])), highlight(", ".join(versioners.keys()))))
            sys.exit(1)
    else:
        print_error("%s needs a parameter in the form of '[versioner]:[parameters]'. See %s for more information." %
                    (highlight("--read-version"), highlight("--help-versioner")))
        sys.exit(1)

    for v in versioners.values():
        v.validate_args(args)


def version(args):
    reader = versioners[args.read_version.split(":")[0]]

