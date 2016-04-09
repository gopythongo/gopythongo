# -* encoding: utf-8 *-


def add_args(parser):
    gr_docker = parser.add_argument_group("docker")
    gr_docker.add_argument("--use-docker", dest="use_docker", action="store_true")


def validate_args():
    pass
