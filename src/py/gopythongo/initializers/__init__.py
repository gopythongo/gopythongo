# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from abc import abstractmethod

import configargparse
import io
import os

from typing import Dict, TextIO, Sequence, Any, cast

from gopythongo.initializers.help import InitializerHelpAction
from gopythongo.utils import plugins, GoPythonGoEnableSuper, highlight, ErrorMessage, get_umasked_mode

_initializers = {}  # type: Dict[str, 'BaseInitializer']


def get_initializers() -> Dict[str, 'BaseInitializer']:
    return _initializers


def init_subsystem() -> None:
    global _initializers

    from gopythongo.initializers import pbuilder_fpm_aptly, docker_copy_docker
    _initializers = {
        "pbuilder_deb": pbuilder_fpm_aptly.initializer_class(".gopythongo"),
        "docker": docker_copy_docker.initializer_class(".gopythongo"),
    }

    plugins.load_plugins("gopythongo.initializers", _initializers, "initializer_class", BaseInitializer,
                         "initializer_name", [".gopythongo"])


def add_args(parser: configargparse.ArgumentParser) -> None:
    gp_init = parser.add_argument_group("Quick start / Configuration generators")
    gp_init.add_argument("--init", action=InitializerAction, nargs="+", metavar=("BUILDTYPE", "PATH"),
                         help="Initialize a default configuration. BUILDTYPE must be one of (%s) and PATH"
                              "is the path of the configuration folder you want to initialize." %
                              (", ".join(_initializers.keys())))
    parser.add_argument("--help-initializer", action=InitializerHelpAction, choices=_initializers.keys(), default=None)


def validate_args(args: configargparse.Namespace) -> None:
    pass


class InvalidArgumentException(Exception):
    pass


class BaseInitializer(GoPythonGoEnableSuper):
    def __init__(self, configfolder: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(configfolder, *args, **kwargs)
        self._configfolder = configfolder

    @property
    def configfolder(self) -> str:
        """
        **@property**
        :return: the relative name of the config folder
        """
        return self._configfolder

    @configfolder.setter
    def configfolder(self, configfolder: str) -> None:
        self._configfolder = configfolder

    def _check_rights(self) -> bool:
        if os.path.exists(self.configfolder):
            if os.access(self.configfolder, os.W_OK & os.X_OK):
                return True
            else:
                raise ErrorMessage("Apparently GoPythonGo has no write access to %s" %
                                   os.path.abspath(highlight(self.configfolder)))
        else:
            if os.access(os.path.dirname(self.configfolder) or ".", os.W_OK & os.X_OK):
                return True
            else:
                raise ErrorMessage("Apparently GoPythonGo has no write access to %s " %
                                   highlight(os.path.abspath(os.path.dirname(self.configfolder) or ".")))

    def ensure_config_folder(self) -> None:
        if self._check_rights() and not os.path.exists(self.configfolder):
            os.mkdir(self.configfolder)

    def create_file_in_config_folder(self, filename: str, mode: int=None) -> TextIO:
        """
        :param filename: the name of the file in the generated config folder
        :param mode: pass an ``int`` here if you want to modify the files mode (will be umasked)
        :return: an open file descriptor (``TextIO``) object that the *caller must call `.close()` on*
        """
        if os.path.isfile(filename):
            raise InvalidArgumentException("Call create_file_in_config_folder with a filename, not a path")

        self.ensure_config_folder()
        f = cast(TextIO, io.open(os.path.join(self.configfolder, filename), mode="wt", encoding="utf-8"))

        if mode:
            os.chmod(os.path.join(self.configfolder, filename), get_umasked_mode(mode))

        return f

    @property
    @abstractmethod
    def initializer_name(self) -> str:
        """
        **@property**
        """
        raise NotImplementedError("Subclasses of BaseInitializer must override initializer_name")

    @abstractmethod
    def build_config(self) -> None:
        """
        The implementation of this method should create all necessary configuration files for the quick start
        config provided by this Initializer and output useful information about how to use it.
        """
        raise NotImplementedError("Subclasses of BaseInitializer must override build_config")

    @abstractmethod
    def print_help(self) -> None:
        raise ErrorMessage("Unfortunately %s does not provide help" % self.initializer_name)


class InitializerAction(configargparse.Action):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def __call__(self, parser: configargparse.ArgumentParser, namespace: configargparse.Namespace,
                 values: Sequence[str], option_string: str=None) -> None:
        if len(values) > 2:
            raise ErrorMessage("%s takes 1 or 2 arguments, not more." % highlight("--init"))

        if values[0] not in _initializers:
            raise ErrorMessage("Unknown initializer \"%s\". Acceptable values are: %s" %
                               (highlight(values[0]), highlight(", ".join(_initializers.keys()))))

        initializer = _initializers[values[0]]

        if len(values) > 1:
            initializer.configfolder = values[1]  # override config folder if it's not the default

        if os.path.exists(initializer.configfolder):
            raise ErrorMessage("%s already exists. If you want to overwrite it, remove it first." %
                               initializer.configfolder)

        initializer.build_config()
        parser.exit(0)
