# -* encoding: utf-8 *-
import argparse

from typing import Any, Sequence, Union, Dict, cast

import gopythongo.shared.aptly_args as _aptly_args

from gopythongo.stores import BaseStore
from gopythongo.utils import print_debug, highlight
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

    @staticmethod
    def _get_aptly_versioner() -> 'AptlyVersioner':
        from gopythongo.versioners import get_versioners
        from gopythongo.versioners.aptly import AptlyVersioner
        aptlyv = cast(AptlyVersioner, get_versioners()["aptly"])
        return aptlyv

    @staticmethod
    def _get_debian_versionparser() -> 'DebianVersionParser':
        from gopythongo.versioners import get_version_parsers
        debvp = get_version_parsers()["debian"]
        return debvp

    def _check_version_exists(self, package_name: str, version: str, args: argparse.Namespace) -> bool:
        aptlyv = self._get_aptly_versioner()
        if aptlyv.query_repo_versions("Name (%s), $Version (= %s)" %
                                      (package_name, version), args,
                                      allow_fallback_version=False):
            return True
        else:
            return False

    def _find_unused_version(self, package_name: str, version: str, action: str,
                             args: argparse.Namespace) -> VersionContainer[DebianVersion]:
        print_debug("Finding a version string in the aptly store for %s based off %s" %
                    (highlight(package_name), highlight(version)))
        aptlyv = self._get_aptly_versioner()
        debvp = self._get_debian_versionparser()

        debversions = aptlyv.query_repo_versions("Name (%s), $Version (%% *%s*)" %
                                                 (package_name, version), args,
                                                 allow_fallback_version=False)

        if debversions:
            # we already have a version from the base version
            # create a new one off the highest version we found
            new_base = debversions[-1]
            print_debug("Found existing versions around base version %s. Highest sorted version %s is the new base "
                        "version for %s" % (highlight(str(new_base)), highlight(package_name)))
            after_action = debvp.execute_action(debvp.deserialize(str(new_base)), action)
            if self._check_version_exists(package_name, str(after_action.version), args):
                print_debug("The new after-action (%s) version %s, based off %s, derived from %s is already taken, so "
                            "we now recursively search for an unused version string for %s" %
                            (action, highlight(str(after_action)), highlight(str(new_base)), highlight(version),
                             highlight(package_name)))
                self._find_unused_version(package_name, str(after_action.version), action, args)
            else:
                print_debug("After executing action %s, the selected next version for %s is %s" %
                            (highlight(action), highlight(package_name), highlight(str(after_action))))
                return debvp.deserialize(str(after_action))
        else:
            print_debug("%s seems to be as yet unused" % highlight(version))
            return debvp.deserialize(version)

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
