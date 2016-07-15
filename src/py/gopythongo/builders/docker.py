# -* encoding: utf-8 *-
import argparse

import gopythongo.shared.docker_args

from gopythongo.utils import print_info, highlight
from gopythongo.builders import BaseBuilder
from typing import Any


class DockerBuilder(BaseBuilder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def builder_name(self) -> str:
        return "docker"

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        gopythongo.shared.docker_args.add_shared_args(parser)

        gp_docker = parser.add_argument_group("Docker Builder options")
        gp_docker.add_argument("--docker-buildfile", dest="docker_buildfile", default=None,
                               help="Specify a Dockerfile to build the the build environment. The build commands will "
                                    "then be executed inside the resulting container.")
        gp_docker.add_argument("--docker-leave-containers", dest="docker_leave_containers", action="store_true",
                               default=False, env_var="DOCKER_LEAVE_CONTAINERS",
                               help="After creating a build environment and a runtime container, if this option is "
                                    "used, GoPythonGo will not use 'docker rm' and 'docker rmi' to clean up the "
                                    "resulting containers.")

    def validate_args(self, args: argparse.Namespace) -> None:
        gopythongo.shared.docker_args.validate_shared_args(args)

    def build(self, args: argparse.Namespace) -> None:
        print_info("Building with %s" % highlight("docker"))


builder_class = DockerBuilder
