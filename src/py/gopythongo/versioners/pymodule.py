# -* encoding: utf-8 *-
import argparse

from typing import Any

import gopythongo.versioners as _versioners

from importlib import import_module
from gopythongo.utils import highlight, ErrorMessage


def import_string(dotted_path: str) -> Any:
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.

    Blatantly copied from Django 1.9.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as e:
        msg = "%s doesn't look like a module path" % dotted_path
        raise ImportError(msg) from e

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as e:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
        raise ImportError(msg) from e


class PymoduleVersioner(_versioners.BaseVersioner):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versioner_name(self) -> str:
        return u"pymodule"

    @property
    def can_read(self) -> bool:
        return True

    @property
    def can_create(self) -> bool:
        return False

    def can_execute_action(self, action: str) -> bool:
        return False

    def print_help(self) -> None:
        print("The pymodule versioner reads version strings from Python modules which must be\n"
              "on PYTHONPATH. It accepts one parameter with is a dotted string identifying the\n"
              "fully qualified module name of a Python module and an attribute to read or\n"
              "function to call, which must be a unicode string (i.e. str on Py3k and unicode\n"
              "on Py2).\n"
              "\n"
              "Examples: --versioner='pymodule' --pymodule-read='gopythongo.version'\n"
              "          --versioner='pymodule' --pymodule-read='a.deeper.module.get_version'\n")

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        gr_pymod = parser.add_argument_group("Pymodule Versioner")
        gr_pymod.add_argument("--pymodule-read", dest="pymodule_read", default=None,
                              help="A fully qualified dotted path to a str attribute in a Python module accessible on"
                                   "the current PYTHONPATH to be read to get the version string.")

    def validate_args(self, args: argparse.Namespace) -> None:
        if args.pymodule_read:
            try:
                import_string(args.pymodule_read)
            except ImportError as e:
                raise ErrorMessage("Pymodule versioner can't import/read %s" % args.pymodule_read) from e
        else:
            raise ErrorMessage("%s requires %s" % (highlight("--versioner=pymodule"), highlight("--pymodule-read")))

    def read(self, args: argparse.Namespace) -> str:
        attr = import_string(args.pymodule_read)
        if callable(attr):
            return attr()
        return attr


versioner_class = PymoduleVersioner
