# -* encoding: utf-8 *-
import sys

from typing import Any

from gopythongo.initializers import BaseInitializer
from gopythongo.utils import highlight, success

configtpl = """
builder=pbuilder
distribution=jessie

# if you use your own package mirror, you MUST add the Debian release keys to
# /etc/apt/trusted.gpg first, otherwise debootstrap will be unable to
# authenticate the packages
#   gpg --no-default-keyring --keyring /etc/apt/trusted.gpg --import \
#   /usr/share/keyrings/debian-archive-keyring.gpg
#
# The following MUST be on one line. You also probably want to put this into
# the PBUILDER_CREATE_OPTS environment variable on your build server.
# Again, use this if you use your own local Debian mirror, otherwise it's
# unnecessary.
# pbuilder-create-opts=--keyring /etc/apt/trusted.gpg --debootstrapopts --keyring=/etc/apt/trusted.gpg --mirror http://fileserver.maurusnet.test/debian
run-after-create=[CONFIGFOLDER/install_fpm.sh]
packer=fpm

store=aptly
repo=mypackage
# To sign your own packages and publish them on your own APT repository, you
# should create a signing keypair, like this:
#   gpg --no-default-keyring --keyring /root/mypackage_sign.gpg --gen-key
#
# Then note the key's ID and the passphrase you protected it with. Put the
# passphrase in a text file on your build server readable only by the build
# server itself. Put your key's ID and the passphrase file location in the
# config line below.
#
# The following MUST be on one line. You MOST LIKELY don't want to keep this
# information in your source control, but really want to set the
# APTLY_PUBLISH_OPTS environment variable on your build server instead.
# aptly-publish-opts=-distribution=jessie -architectures=amd64 -keyring=/root/mypackage_sign.gpg -gpg-key=KEY_ID_HERE -passphrase-file=/root/mypackage_passphrase.txt

# If you want to publish to S3, you must configure aptly with a AWS Key ID and
# secret key in aptly.conf.
# aptly-publish-endpoint=s3:aptlyrepo:debian/

# Change the lines below to read your project's version from somewhere else
# if you want to.
versioner=pymodule
pymodule-read=mypackage.version
version-parser=pep440
version-action=bump-revision

use-fpm=/usr/local/bin/fpm
run-fpm=template:CONFIGFOLDER/fpm_opts

eatmydata
eatmydata-path=/usr/bin/eatmydata
"""

installfpm = """
#!/bin/bash

# This script is used to create a pbuilder build environment that has FPM
# installed so GoPythonGo can create a .deb package of your project

# do nothing if fpm already exists
test -e /usr/local/bin/fpm && exit 0

EATMYDATA=""
if test -e /usr/bin/eatmydata; then
    EATMYDATA="/usr/bin/eatmydata"
fi

# make sure we have gem
if ! test -e /usr/bin/gem; then
    $EATMYDATA apt-get update
    $EATMYDATA apt-get --no-install-recommends -y install ruby ruby-dev
fi

$EATMYDATA gem install fpm
"""

fpm_opts = """
-p PACKAGENAME-{{debian_version.version}}.deb
-n PACKAGENAME
-v "{{debian_version.version}}"
-m "Your Name <youremail@example.com>"
-d "python3 python3-pip python3-virtualenv"
{{basedir}}
"""


class PbuilderFpmAptlyInitializer(BaseInitializer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def initializer_name(self) -> str:
        return "pbuilder_deb"

    def build_config(self) -> None:
        cf = self.create_file_in_config_folder("config")
        cf.write(configtpl.replace("CONFIGFOLDER", self.configfolder))
        cf.close()

        instf = self.create_file_in_config_folder("install_fpm.sh")
        instf.write(installfpm)
        instf.close()

        fpm = self.create_file_in_config_folder("fpm_opts")
        fpm.write(fpm_opts)
        fpm.close()

        success("***** SUCCESS *****")
        print("GoPythonGo created the following files for you:\n"
              "\n"
              "  %s/config\n"
              "  %s/install_fpm.sh\n"
              "  %s/fpm_opts\n"
              "\n"
              "Please make sure to edit and adapt them as necessary to your project.\n" %
              (self.configfolder, self.configfolder, self.configfolder))

    def print_help(self) -> None:
        print("Pbuilder and .deb quick start\n"
              "=============================\n"
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
              "        apt-get --no-install-recommends install pbuilder ruby ruby-dev aptly \\\n"
              "            eatmydata\n"
              "        gem install fpm\n"
              "\n"
              "You can find more information at the following URLs:\n"
              "    http://gopythongo.com/\n"
              "    https://aptly.info/\n"
              "    https://github.com/jordansissel/fpm\n" %
              (highlight("fpm"), highlight("apt-get"), highlight("As root run:")))
        sys.exit(0)


initializer_class = PbuilderFpmAptlyInitializer
