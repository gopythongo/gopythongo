# -* encoding: utf-8 *-


def add_args(parser):
    grp_pbuilder = parser.add_argument_group("docker")
    grp_pbuilder.add_argument("--use-docker", dest="use_docker", action="store_true")


def validate_args():
    pass
