# -* encoding: utf-8 *-
import sys

from typing import Any

from gopythongo.initializers import BaseInitializer
from gopythongo.utils import highlight


class PbuilderFpmAptlyInitializer(BaseInitializer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def initializer_name(self) -> str:
        return "pbuilder_deb"

    def build_config(self) -> str:
        return ""

    def print_help(self) -> None:
        print("Pbuilder and .deb Quickstart\n"
              "============================\n"
              "\n"
              "This Initializer generates an example configuration for GoPythonGo that depends\n"
              "on the Debian Pbuilder chroot build system. This allows you to build a\n"
              "virtualenv in an independent environment, then pack it up using %s and move it\n"
              "into a APT repository using aptly. This will allow you to easily ship your\n"
              "projects to your servers using %s.\n"
              "\n"
              "Install the necessary dependencies:\n"
              "\n"
              "    %s\n"
              "        echo deb http://repo.aptly.info/ squeeze main \\\n"
              "          > /etc/apt/sources.list.d/aptly.info\n"
              "        apt-get update\n"
              "        apt-get --no-install-recommends install pbuilder ruby ruby-dev aptly\n" %
              (highlight("fpm"), highlight("apt-get"), highlight("As root run:")))
        sys.exit(0)


initializer_class = PbuilderFpmAptlyInitializer
