# -* encoding: utf-8 *-

import os
import sys

from gopythongo.utils import print_error, highlight


_docker_shared_args_added = False


def add_shared_args(parser):
    global _docker_shared_args_added

    if not _docker_shared_args_added:
        gr_docker_shared = parser.add_argument_group("Docker common parameters")
        gr_docker_shared.add_argument("--use-docker", dest="docker_executable", default="/usr/bin/docker",
                                      help="Specify an alternative docker executable.")

    _docker_shared_args_added = True


def validate_shared_args(args):
    if not os.path.exists(args.docker_executable) or not os.access(args.docker_executable, os.X_OK):
        print_error("docker not found in path or not executable (%s). You can specify\n"
                    "an alternative path using %s" % (args.docker_executable,
                                                      highlight("--use-docker")))
        sys.exit(1)
