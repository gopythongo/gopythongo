# -* encoding: utf-8 *-

from gopythongo.versioners import aptly, pymodule


versioners = {
    "aptly": aptly,
    "pymodule": pymodule,
}


def add_args(parser):
    gp_version = parser.add_argument_group("Version determination")
    gp_version.add_argument("--help-versioner", choices=versioners.keys(),
                            help="Show help for a versioner.")
    gp_version.add_argument("--read-version", dest="read_version",
                            help="Specify from where to read the base version string. See --help-versioner for "
                                 "details.")
    gp_version.add_argument("--parse-version-format", dest="parse_version",
                            help="Parse the version string read by --read-version in a specific way.")
    gp_version.add_argument("--new-version-format", dest="new_version",
                            help="Specify a format for the version string to be used for the output package. See "
                                 "--help-versioner for details.")
    gp_version.add_argument("--version-action", dest="version_action",
                            choices=["increment-epoch", "increment-revision", "none"], default="none",
                            help="Choose what to do to the version determined via --read-version to change the "
                                 "version for the output package before it is formatted according to "
                                 "--new-version-format.")


def validate_args(args):
    return True
