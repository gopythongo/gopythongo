# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from abc import abstractmethod

import configargparse

from typing import Dict, Any

from gopythongo.assemblers.help import AssemblerHelpAction
from gopythongo.utils import run_process, create_script_path, print_info, highlight, plugins, \
    CommandLinePlugin, ErrorMessage

_assemblers = {}  # type: Dict[str, 'BaseAssembler']


def get_assemblers() -> Dict[str, 'BaseAssembler']:
    return _assemblers


def get_assemblers_by_type(type: str) -> Dict[str, 'BaseAssembler']:
    return {k: v for k, v in _assemblers.items() if v.assembler_type == type}


def init_subsystem() -> None:
    global _assemblers

    from gopythongo.assemblers import django, virtualenv, certifybuild
    _assemblers = {
        "django": django.assembler_class(),
        "virtualenv": virtualenv.assembler_class(),
        "certifybuild": certifybuild.assembler_class(),
    }

    plugins.load_plugins("gopythongo.assemblers", _assemblers, "assembler_class", BaseAssembler, "assembler_name")


class BaseAssembler(CommandLinePlugin):
    TYPE_ISOLATED = "isolated"
    TYPE_PREISOLATION = "preisolation"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    @abstractmethod
    def assembler_name(self) -> str:
        """
        **@property**
        """
        raise NotImplementedError("Each subclass of BaseAssembler MUST implement assembler_name")

    @property
    @abstractmethod
    def assembler_type(self) -> str:
        """
        **@property**
        """
        raise NotImplementedError("Each subclass of BaseAssembler MUST implement assembler_type")

    @abstractmethod
    def assemble(self, args: configargparse.Namespace) -> None:
        raise NotImplementedError("Each subclass of BaseAssembler MUST implement assemble")

    @abstractmethod
    def print_help(self) -> None:
        raise NotImplementedError("Each subclass of BaseAssembler MUST implement print_help")


def add_args(parser: configargparse.ArgumentParser) -> None:
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

    parser.add_argument("--help-assembler", action=AssemblerHelpAction, choices=_assemblers.keys(), default=None)

    for assembler in _assemblers.values():
        assembler.add_args(parser)


def validate_args(args: configargparse.Namespace) -> None:
    if args.assemblers:
        for asm in args.assemblers:
            if asm in _assemblers.keys():
                _assemblers[asm].validate_args(args)
            else:
                raise ErrorMessage("Unknown assembler: %s. Known assemblers are: %s" %
                                   (highlight(asm), highlight(", ".join(_assemblers.keys()))))

    if not os.path.isabs(args.build_path):
        raise ErrorMessage("build_path must be an absolute path. %s is not absolute." % highlight(args.build_path))


def assemble(args: configargparse.Namespace, assembler_type: str) -> None:
    for asm in args.assemblers:
        if _assemblers[asm].assembler_type == assembler_type:
            _assemblers[asm].assemble(args)
