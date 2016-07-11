# -* encoding: utf-8 *-
import argparse

from typing import Any, Sequence, Union, Dict, cast

import gopythongo.shared.aptly_args as _aptly_args

from gopythongo.stores import BaseStore
from gopythongo.utils.debversion import DebianVersion
from gopythongo.versioners.parsers import VersionContainer


class AptlyStore(BaseStore):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def store_name(self) -> str:
        return u"aptly"

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        _aptly_args.add_shared_args(parser)

    def validate_args(self, args: argparse.Namespace) -> None:
        _aptly_args.validate_shared_args(args)

    def _find_unused_version(self, package_name: str, version: str, action: str,
                             args: argparse.Namespace) -> VersionContainer:
        from gopythongo.versioners import get_versioners, get_version_parsers
        from gopythongo.versioners.aptly import AptlyVersioner
        aptlyv = cast(AptlyVersioner, get_versioners()["aptly"])
        debvp = get_version_parsers()["debian"]

        debversions = aptlyv.query_repo_versions("Name (%s), $Version (= %s)" %
                                                 (package_name, version), args,
                                                 allow_fallback_version=False)

        if debversions:
            # we already have a version from the base version
            # create a new one off the highest version we found
            new_base = debversions[-1]
            after_action = debvp.execute_action(debvp.deserialize(str(new_base)), action)

    def generate_future_versions(self, artifact_names: Sequence[str], base_version: VersionContainer[Any],
                                 args: argparse.Namespace) -> Union[Dict[str, VersionContainer[DebianVersion]], None]:
        ret = {}  # type: Dict[str, VersionContainer[DebianVersion]]
        base_debv = base_version.convert_to("debian")
        for package_name in artifact_names:
            next_version = self._find_unused_version(package_name, str(base_debv.version), args.version_action, args)
            ret[package_name] = next_version
        return ret

    def store(self, args: argparse.Namespace) -> None:
        pass


store_class = AptlyStore
