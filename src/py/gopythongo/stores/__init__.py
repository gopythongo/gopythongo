# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import configargparse

from typing import Dict, Any, Sequence, Union, List

from gopythongo.stores.help import StoreHelpAction
from gopythongo.utils import plugins, CommandLinePlugin, ErrorMessage
from gopythongo.versioners.parsers import VersionContainer

_stores = {}  # type: Dict[str, 'BaseStore']


def get_stores() -> Dict[str, 'BaseStore']:
    return _stores


def init_subsystem() -> None:
    global _stores

    from gopythongo.stores import aptly, aptly_remote, docker
    _stores = {
        "aptly": aptly.store_class(),
        "remote-aptly": aptly_remote.store_class(),
        "docker": docker.store_class(),
    }

    plugins.load_plugins("gopythongo.stores", _stores, "store_class", BaseStore, "store_name")


class BaseStore(CommandLinePlugin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def store_name(self) -> str:
        """
        **@property**

        Return the identifier and command-line parameter value for --store used by this Store.
        :returns: the identifier
        :rtype: str
        """
        raise NotImplementedError("Each subclass of BaseStore MUST implement store_name")

    @property
    def supported_version_parsers(self) -> List[str]:
        """
        **@property**
        :return: a list of one or more supported version parsers
        """
        raise NotImplementedError("Each subclass of BaseStore MUST implement supported_version_parsers")

    def generate_future_versions(self, artifact_names: Sequence[str], base_version: VersionContainer,
                                 action: str,
                                 args: configargparse.Namespace) -> Union[Dict[str, VersionContainer], None]:
        """
        Takes a list of unique artifact identifiers (e.g. package names) which *will be created by a Packer during the
        build later* and returns a dict mapping of identifier to version for the Packer to be used during the build
        or ``None`` if the store can't generate future versions. The store should use ``action`` to generate the
        version strings for all artifacts.

        :param artifact_names: a list of artifact identifiers
        :param base_version: the base version from which to generate future versions
        :param action: the version action selected by the user to generate future versions
        :param args: command-line parameters
        :return: a mapping of artifact identifiers to version information
        """
        raise NotImplementedError("Each subclass of BaseStore MUST implement generate_future_versions")

    def store(self, args: configargparse.Namespace) -> None:
        raise NotImplementedError("Each subclass of BaseStore MUST implement store")

    def print_help(self) -> None:
        raise NotImplementedError("Each subclass of BaseStore MUST implement print_help")


def add_args(parser: configargparse.ArgumentParser) -> None:
    parser.add_argument("--help-store", action=StoreHelpAction, choices=_stores.keys(), default=None)

    for s in _stores.values():
        s.add_args(parser)


def validate_args(args: configargparse.Namespace) -> None:
    if args.store in _stores.keys():
        _stores[args.store].validate_args(args)


def store(args: configargparse.Namespace) -> None:
    from gopythongo.utils.buildcontext import the_context
    if len(the_context.packer_artifacts) == 0:
        raise ErrorMessage("The Builder/Packer seems to have created no build artifacts for GoPythonGo to process.")
    _stores[args.store].store(args)
