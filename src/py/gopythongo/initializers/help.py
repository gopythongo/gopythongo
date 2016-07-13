# -* encoding: utf-8 *-
import argparse

from typing import Iterable, Any

from gopythongo.utils import highlight


class InitializerHelpAction(argparse.Action):
    def __init__(self,
                 option_strings: str,
                 dest: str,
                 default: Any=None,
                 choices: Iterable[Any]=None,
                 help: str="Show help for GoPythonGo Configuration Initializers.") -> None:
        super().__init__(option_strings=option_strings, dest=dest, default=default, nargs="?",
                         choices=choices, help=help)

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 values: str, option_string: str=None) -> None:
        from gopythongo.initializers import get_initializers
        initializers = get_initializers()
        if values in initializers.keys():
            initializers[values].print_help()
        else:
            print("Quick start configuration generators\n"
                  "====================================\n"
                  "\n"
                  "When you want to start working with GoPythonGo in a project, you need to\n"
                  "configure GoPythonGo for your workflow. This means that you need to select\n"
                  "a builder, one or more assemblers, a packer and a store fitting your processes\n"
                  "and deployment options.\n"
                  "\n"
                  "To make it easier to get started, GoPythonGo can generate common configurations\n"
                  "for you as a starting point. The modules generating these quick start\n"
                  "configurations are called \"%s\". It's also easy to write a plugin to\n"
                  "support common defaults in your organization. GoPythonGo ships with some default\n"
                  "Initializers. Those are:\n"
                  "\n"
                  "    %s - build a virtualenv using Debian's pbuilder isolation system\n"
                  "                   and package it in a .deb. Then store it in an APT repository\n"
                  "                   using aptly.\n"
                  "\n"
                  "    %s       - build a virtualenv in a Docker-based build environment then\n"
                  "                   copy it into a Docker production container and push that to\n"
                  "                   a Docker container registry,\n"
                  "\n"
                  "You generate a quick start configuration by using --init [configtype] [path],\n"
                  "where path is optional (default: .config/). You can get more information on the\n"
                  "individual Initializers by using\n"
                  "%s." %
                  (highlight("Initializers"), highlight("pbuilder_deb"), highlight("docker"),
                   highlight("--help-initializer=[%s]" % ", ".join(initializers.keys()))))

            parser.exit()
