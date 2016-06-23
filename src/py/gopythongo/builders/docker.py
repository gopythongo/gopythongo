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
        return u"docker"

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        gopythongo.shared.docker_args.add_shared_args(parser)

    def validate_args(self, args: argparse.Namespace) -> None:
        gopythongo.shared.docker_args.validate_shared_args(args)

    def build(self, args: argparse.Namespace) -> None:
        print_info("Building with %s" % highlight("docker"))


builder_class = DockerBuilder
