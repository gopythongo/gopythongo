# -* encoding: utf-8 *-
import argparse

import gopythongo.shared.docker_args
from gopythongo.stores import BaseStore


class DockerStore(BaseStore):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @property
    def store_name(self) -> str:
        return u"docker"

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        gopythongo.shared.docker_args.add_shared_args(parser)

    def validate_args(self, args: argparse.Namespace) -> None:
        pass

    def store(self, args: argparse.Namespace) -> None:
        pass


store_class = DockerStore
