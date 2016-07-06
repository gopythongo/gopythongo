# -* encoding: utf-8 *-
import argparse

from typing import Dict, Any

from gopythongo.utils import plugins, CommandLinePlugin, ErrorMessage

stores = {}  # type: Dict[str, 'BaseStore']


def init_subsystem() -> None:
    global stores

    from gopythongo.stores import aptly, docker
    stores = {
        u"aptly": aptly.store_class(),
        u"docker": docker.store_class(),
    }

    plugins.load_plugins("gopythongo.stores", stores, "store_class", BaseStore, "store_name")


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

    def store(self, args: argparse.Namespace) -> None:
        pass


def add_args(parser: argparse.ArgumentParser) -> None:
    global stores

    for s in stores.values():
        s.add_args(parser)


def validate_args(args: argparse.Namespace) -> None:
    if args.store in stores.keys():
        stores[args.store].validate_args(args)


def store(args: argparse.Namespace) -> None:
    stores[args.store].store(args)
