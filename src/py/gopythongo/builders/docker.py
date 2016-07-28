# -* encoding: utf-8 *-
import configargparse

from typing import Any, Type

import gopythongo.shared.docker_args

from gopythongo.utils import print_info, highlight
from gopythongo.builders import BaseBuilder


class DockerBuilder(BaseBuilder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def builder_name(self) -> str:
        return "docker"

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        gopythongo.shared.docker_args.add_shared_args(parser)

        gp_docker = parser.add_argument_group("Docker Builder options")
        gp_docker.add_argument("--docker-buildfile", dest="docker_buildfile", default=None,
                               help="Specify a Dockerfile to build the the build environment. The build commands will "
                                    "then be executed inside the resulting container. You can use templating here. ")
        gp_docker.add_argument("--docker-leave-containers", dest="docker_leave_containers", action="store_true",
                               default=False, env_var="DOCKER_LEAVE_CONTAINERS",
                               help="After creating a build environment and a runtime container, if this option is "
                                    "used, GoPythonGo will not use 'docker rm' and 'docker rmi' to clean up the "
                                    "resulting containers.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        gopythongo.shared.docker_args.validate_shared_args(args)

    def build(self, args: configargparse.Namespace) -> None:
        print_info("Building with %s" % highlight("docker"))

    def print_help(self) -> None:
        print("Docker Builder\n"
              "==============\n"
              "\n"
              "Builds virtualenvs in a Docker container. This requires GoPythonGo to either\n"
              "run as root or the user running GoPythonGo to be a member of the docker group.\n"
              "To run Docker GoPythonGo relies on templated build Dockerfile which you can\n"
              "customize to represent your later production runtime setup. Please note that\n"
              "the build container used by the Docker Builder is not a container which you\n"
              "should ship later, since it will likely contain compilers, header files and\n"
              "other helpers. Instead create a minimal production Docker container from the\n"
              "build container's output later, using the GoPythonGo Docker Store, for example.\n"
              "\n"
              "The build Dockerfile template must contain the following variables that\n"
              "GoPythonGo relies on to execute itself inside the build container:\n"
              "\n"
              "    {{mounts}}   - will resolve to a number of MOUNT instructions\n"
              "    {{commands}} - will be replaced by the GoPythonGo build commands\n")


builder_class = DockerBuilder  # type: Type[DockerBuilder]
