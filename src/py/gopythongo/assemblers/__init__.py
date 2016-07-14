# -* encoding: utf-8 *-
import argparse
import os

from typing import Dict, Any

from gopythongo.utils import run_process, create_script_path, print_info, highlight, plugins, \
    CommandLinePlugin, ErrorMessage

_assemblers = {}  # type: Dict[str, 'BaseAssembler']


def get_assemblers() -> Dict[str, 'BaseAssembler']:
    return _assemblers


def init_subsystem() -> None:
    global _assemblers

    from gopythongo.assemblers import django, virtualenv
    _assemblers = {
        "django": django.assembler_class(),
        "virtualenv": virtualenv.assembler_class(),
    }

    plugins.load_plugins("gopythongo.assemblers", _assemblers, "assembler_class", BaseAssembler, "assembler_name")


class BaseAssembler(CommandLinePlugin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def assembler_name(self) -> str:
        """
        **@property**
        """
        raise NotImplementedError("Each subclass of BaseAssembler MUST implement assembler_name")

    def assemble(self, args: argparse.Namespace) -> None:
        raise NotImplementedError("Each subclass of BaseAssembler MUST implement assemble")


def add_args(parser: argparse.ArgumentParser) -> None:
    global _assemblers

    pos_args = parser.add_argument_group("Python ecosystem arguments (positional)")
    pos_args.add_argument("build_path",
                          help="set the location where the virtual environment will be built, this " +
                               "is IMPORTANT as it is also the location where the virtualenv must " +
                               "ALWAYS reside (i.e. the install directory. Virtualenvs are NOT relocatable" +
                               "by default! All path parameters are relative to this path")
    pos_args.add_argument("packages", metavar="package<=>version", nargs="*",
                          help="a list of package/version specifiers. Remember to quote your " +
                               "strings as in \"Django>=1.9,<1.10\"")

    for assembler in _assemblers.values():
        assembler.add_args(parser)


def validate_args(args: argparse.Namespace) -> None:
    if not os.path.isabs(args.build_path):
        raise ErrorMessage("build_path must be an absolute path. %s is not absolute." % highlight(args.build_path))

    for assembler in args.assemblers:
        if assembler in _assemblers.keys():
            _assemblers[assembler].validate_args(args)


def assemble(args: argparse.Namespace) -> None:
    for assembler in _assemblers.values():
        assembler.assemble(args)
