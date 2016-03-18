# -* encoding: utf-8 *-


def add_args(parser):
    grp_pbuilder = parser.add_argument_group("pbuilder")
    grp_pbuilder.add_argument("--use-pbuilder", dest="use_pbuilder", action="store_true")


def validate_args():
    pass
