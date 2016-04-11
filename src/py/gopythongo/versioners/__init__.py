# -* encoding: utf-8 *-


def add_args(parser):
    gp_version = parser.add_argument_group("Version determination")
    gp_version.add_argument("--readversion", dest="readversion",
                            help="Read a version string")
