# -* encoding: utf-8 *-
import argparse

import gopythongo.shared.aptly_args as _aptly_args

from gopythongo.stores import BaseStore


class AptlyStore(BaseStore):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @property
    def store_name(self) -> str:
        return u"aptly"

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        _aptly_args.add_shared_args(parser)

    def validate_args(self, args: argparse.Namespace) -> None:
        # _aptly_args.validate_shared_args(args)
        pass

    def store(self, args: argparse.Namespace) -> None:
        pass


store_class = AptlyStore
