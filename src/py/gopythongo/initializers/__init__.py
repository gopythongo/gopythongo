# -* encoding: utf-8 *-
import argparse
import io
import os

from typing import Dict, TextIO, Sequence, Any

from gopythongo.initializers.help import InitializerHelpAction
from gopythongo.utils import plugins, GoPythonGoEnableSuper, highlight, ErrorMessage

initializers = {}  # type: Dict[str, 'BaseInitializer']


def init_subsystem() -> None:
    global initializers

    from gopythongo.initializers import pbuilder_fpm_aptly, docker_copy_docker
    initializers = {
        "pbuilder_deb": pbuilder_fpm_aptly.initializer_class(".gopythongo"),
        "docker": docker_copy_docker.initializer_class(".gopythongo"),
    }

    plugins.load_plugins("gopythongo.initializers", initializers, "initializer_class", BaseInitializer,
                         "initializer_name", [".gopythongo"])


def add_args(parser: argparse.ArgumentParser) -> None:
    gp_init = parser.add_argument_group("Quick start / Configuration generators")
    gp_init.add_argument("--init", action=InitializerAction, nargs="+", metavar=("BUILDTYPE", "PATH"),
                         help="Initialize a default configuration. BUILDTYPE must be one of (%s) and PATH"
                              "is the path of the configuration folder you want to initialize." %
                              (", ".join(initializers.keys())))
    gp_init.add_argument("--help-initializer", action=InitializerHelpAction, choices=initializers.keys(), default=None,
                         help="Get help on individual quick start configuration generators or general help on "
                              "configuration generators.")


def validate_args(args: argparse.Namespace) -> None:
    pass


class InvalidArgumentException(Exception):
    pass


class BaseInitializer(GoPythonGoEnableSuper):
    def __init__(self, configfolder: str, *args: Any, **kwargs: Any) -> None:
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
                raise ErrorMessage("Apparently GoPythonGo has no write access to %s" %
                                   highlight(self.configfolder))
        else:
            if os.access(os.path.dirname(self.configfolder), os.W_OK & os.X_OK):
                return True
            else:
                raise ErrorMessage("Apparently GoPythonGo has no write access to %s " %
                                   highlight(os.path.dirname(self.configfolder)))

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
        f = io.open(os.path.join(self.configfolder, filename), mode="wt", encoding="utf-8")
        return io.TextIOWrapper(f)

    @property
    def initializer_name(self) -> str:
        raise NotImplementedError("Subclasses of BaseInitializer must override initializer_name")

    def build_config(self) -> str:
        raise NotImplementedError("Subclasses of BaseInitializer must override build_config")

    def print_help(self) -> None:
        raise ErrorMessage("Unfortunately %s does not provide help" % self.initializer_name)


class InitializerAction(argparse.Action):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Sequence[str],
                 option_string: str=None) -> None:
        if len(values) > 2:
            raise ErrorMessage("%s takes 1 or 2 arguments, not more." % highlight("--init"))

        if values[0] not in initializers:
            raise ErrorMessage("Unknown initializer \"%s\". Acceptable values are: %s" %
                               (highlight(values[0]), highlight(", ".join(initializers.keys()))))

        initializer = initializers[values[0]]

        if len(values) > 1:
            initializer.configfolder = values[1]  # override config folder if it's not the default

        cf = initializer.create_file_in_config_folder("config")
        cf.write(initializer.build_config())
        cf.close()
