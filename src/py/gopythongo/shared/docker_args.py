# -* encoding: utf-8 *-

_docker_shared_args_added = False


def add_shared_args(parser):
    global _docker_shared_args_added

    if not _docker_shared_args_added:
        gr_docker_shared = parser.add_argument_group("Docker common parameters")
        gr_docker_shared.add_argument("--use-docker", dest="docker_executable", default="/usr/bin/docker",
                                      help="Specify an alternative docker executable.")

    _docker_shared_args_added = True
