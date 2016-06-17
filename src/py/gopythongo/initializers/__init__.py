# -* encoding: utf-8 *-
import sys

from argparse import Action
from typing import Dict, TextIO

from gopythongo.utils import plugins, print_error


initializers = {}  # type: Dict[str, 'BaseInitializer']


def initialize_subsystem() -> None:
    global initializers

    from gopythongo.initializers import pbuilder_fpm_aptly, docker_copy_docker
    initializers = {
        "pbuilder_fpm_aptly": pbuilder_fpm_aptly.initializer_class(),
        "docker_copy_docker": docker_copy_docker.initializer_class(),
    }

    try:
        plugins.load_plugins("gopythongo.initializers", initializers, "initializer_class", BaseInitializer,
                             "initializer_name")
    except ImportError as e:
        print_error(str(e))
        sys.exit(1)


class BaseInitializer(Action):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def create_config_folder(self) -> None:
        # TODO: implement me
        pass

    def create_file_in_config_folder(self, filename) -> TextIO:
        # TODO: implement me
        pass

    @property
    def initializer_name(self) -> str:
        raise NotImplementedError("Subclasses of BaseInitializer must override initializer_name")

    def build_config(self) -> str:
        raise NotImplementedError("Subclasses of BaseInitializer must override build_config")

    def __call__(self, parser, namespace, values, option_string=None) -> None:
        self.create_config_folder()

        cf = self.create_file_in_config_folder("config")
        cf.write(self.build_config())
        cf.close()
