# -* encoding: utf-8 *-
import argparse

import os
import sys

from argparse import Action
from typing import Dict, TextIO

from gopythongo.utils import plugins, print_error, GoPythonGoEnableSuper, highlight, print_info

initializers = {}  # type: Dict[str, 'BaseInitializer']


def initialize_subsystem() -> None:
    global initializers

    from gopythongo.initializers import pbuilder_fpm_aptly, docker_copy_docker
    initializers = {
        "pbuilder_deb": pbuilder_fpm_aptly.initializer_class(".gopythongo"),
        "docker": docker_copy_docker.initializer_class(".gopythongo"),
    }

    try:
        plugins.load_plugins("gopythongo.initializers", initializers, "initializer_class", BaseInitializer,
                             "initializer_name", [".gopythongo"])
    except ImportError as e:
        print_error(str(e))
        sys.exit(1)


def add_args(parser: argparse.ArgumentParser) -> None:
    pass


def validate_args(args: argparse.Namespace) -> None:
    pass


class InvalidArgumentException(Exception):
    pass


class BaseInitializer(GoPythonGoEnableSuper):
    def __init__(self, configfolder: str, *args, **kwargs) -> None:
        super().__init__(configfolder, *args, **kwargs)
        self._configfolder = configfolder

    @property
    def configfolder(self) -> str:
        return self._configfolder

    @configfolder.setter
    def configfolder(self, configfolder: str) -> None:
        self._configfolder = configfolder

    def _check_rights(self) -> bool:
        if os.path.exists(self.configfolder):
            if os.access(self.configfolder, os.W_OK & os.X_OK):
                return True
            else:
                print_error("Apparently GoPythonGo has no write access to %s" %
                            highlight(self.configfolder))
                sys.exit(1)
        else:
            if os.access(os.path.dirname(self.configfolder), os.W_OK & os.X_OK):
                return True
            else:
                print_info("Apparently GoPythonGo has no write access to %s " %
                           highlight(os.path.dirname(self.configfolder)))
                return True

    def ensure_config_folder(self) -> None:
        if self._check_rights() and not os.path.exists(self.configfolder):
            os.mkdir(self.configfolder)

    def create_file_in_config_folder(self, filename: str) -> TextIO:
        """
        :param filename: the name of the file in the generated config folder
        :return: an open file descriptor (``TextIO``) object that the *caller must call `.close()` on*
        """
        if os.path.isabs(filename):
            raise InvalidArgumentException("Call create_file_in_config_folder with a filename, not a path")

        self.ensure_config_folder()
        f = open(os.path.join(self.configfolder, filename), mode="wt", encoding="utf-8")
        return f

    @property
    def initializer_name(self) -> str:
        raise NotImplementedError("Subclasses of BaseInitializer must override initializer_name")

    def build_config(self) -> str:
        raise NotImplementedError("Subclasses of BaseInitializer must override build_config")


class InitializerAction(Action):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None) -> None:
        initializer = initializers[values]
        initializer.configfolder = values
        initializer.create_config_folder()

        cf = initializer.create_file_in_config_folder("config")
        cf.write(initializer.build_config())
        cf.close()
