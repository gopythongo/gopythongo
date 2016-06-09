# -* encoding: utf-8 *-
import argparse

import gopythongo.versioners as _versioners


class StaticVersioner(_versioners.BaseVersioner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def versioner_name(self) -> str:
        return u"static"

    @property
    def can_read(self) -> bool:
        return False

    @property
    def can_create(self) -> bool:
        return True

    def print_help(self) -> None:
        pass

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        pass

    def validate_args(self, args: argparse.Namespace) -> None:
        pass

    def create(self, args: argparse.Namespace) -> str:
        pass


versioner_class = StaticVersioner
