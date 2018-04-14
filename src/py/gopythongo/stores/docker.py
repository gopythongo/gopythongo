# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import configargparse

from typing import Any, Type, Sequence, Union, Dict, List

import gopythongo.shared.docker_args as _docker_args

from gopythongo.stores import BaseStore
from gopythongo.versioners import VersionContainer


class DockerStore(BaseStore):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def store_name(self) -> str:
        return u"docker"

    @property
    def supported_version_parsers(self) -> List[str]:
        pass

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        _docker_args.add_shared_args(parser)

    def validate_args(self, args: configargparse.Namespace) -> None:
        pass

    def store(self, args: configargparse.Namespace) -> None:
        pass

    def generate_future_versions(self, artifact_names: Sequence[str], base_version: VersionContainer,
                                 action: str,
                                 args: configargparse.Namespace) -> Union[Dict[str, VersionContainer], None]:
        pass

    def print_help(self) -> None:
        pass


store_class = DockerStore  # type: Type[DockerStore]
