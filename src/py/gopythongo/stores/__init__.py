# -* encoding: utf-8 *-
import argparse

from typing import Dict, Any, Sequence, Union, List

from gopythongo.utils import plugins, CommandLinePlugin, ErrorMessage
from gopythongo.versioners.parsers import VersionContainer

_stores = {}  # type: Dict[str, 'BaseStore']


def get_stores() -> Dict[str, 'BaseStore']:
    return _stores


def init_subsystem() -> None:
    global _stores

    from gopythongo.stores import aptly, docker
    _stores = {
        u"aptly": aptly.store_class(),
        u"docker": docker.store_class(),
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
                                 action: str, args: argparse.Namespace) -> Union[Dict[str, VersionContainer], None]:
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

    def store(self, args: argparse.Namespace) -> None:
        raise NotImplementedError("Each subclass of BaseStore MUST implement store")


def add_args(parser: argparse.ArgumentParser) -> None:
    for s in _stores.values():
        s.add_args(parser)


def validate_args(args: argparse.Namespace) -> None:
    if args.store in _stores.keys():
        _stores[args.store].validate_args(args)


def store(args: argparse.Namespace) -> None:
    from gopythongo.utils.buildcontext import the_context
    if len(the_context.packer_artifacts) == 0:
        raise ErrorMessage("The Builder/Packer seems to have created no build artifacts for GoPythonGo to process.")
    _stores[args.store].store(args)
