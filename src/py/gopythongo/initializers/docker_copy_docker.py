# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys

from typing import Any, Type

from gopythongo.initializers import BaseInitializer
from gopythongo.utils import highlight, print_error


class DockerCopyDockerInitializer(BaseInitializer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def initializer_name(self) -> str:
        return "docker"

    def build_config(self) -> None:
        print_error("Not implemented yet :(")

    def print_help(self) -> None:
        print("Docker quick start\n"
              "==================\n"
              "\n"
              "This Initializer generates an example configuration for GoPythonGo that builds\n"
              "a virtualenv in a Docker build container and then installs it into a second\n"
              "production container giving you the most minimal possible runtime. That\n"
              "container is then ideal for uploading to a Docker registry, making it easy to\n"
              "ship that container to your servers using %s.\n" %
              (highlight("docker pull")))
        sys.exit(0)


initializer_class = DockerCopyDockerInitializer  # type: Type[DockerCopyDockerInitializer]
