# -* encoding: utf-8 *-
import sys

from typing import Any

from gopythongo.initializers import BaseInitializer
from gopythongo.utils import highlight


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
# pbuilder-create-opts=--keyring /etc/apt/trusted.gpg --debootstrapopts --keyring=/etc/apt/trusted.gpg --mirror http://fileserver.maurusnet.test/debian
run-after-create=[.gopythongo/install_fpm.sh]
packer=fpm

store=aptly
repo=gopythongo
# To sign your own packages and publish them on your own APT repository, you
# should create a signing keypair, like this:
#   gpg --no-default-keyring --keyring /root/gopythongo_sign.gpg --gen-key
#
# The following MUST be on oen line. You MOST LIKELY don't want to keep this
# information in your source control, but really want to set the
# APTLY_PUBLISH_OPTS environment variable on your build server instead.
# aptly-publish-opts=-distribution=jessie -architectures=amd64 -keyring=/root/gopythongo_sign.gpg -gpg-key=84BEC887FD2B8F2A6F073DC4D0F0F4B5DC236955 -passphrase-file=/root/gopythongo_dev_passphrase.txt
aptly-publish-endpoint=s3:gopythongo:debian/

versioner=pymodule
pymodule-read=gopythongo.version
version-parser=pep440
version-action=bump-revision

use-fpm=/usr/local/bin/fpm
run-fpm=template:.gopythongo/fpm_opts
copy-out=/home/vagrant/test/build

eatmydata
eatmydata-path=/usr/bin/eatmydata
"""

installfpm = """
#!/bin/bash

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
-p gopythongo-{{debian_version.version}}.deb
-n gopythongo
-v "{{debian_version.version}}"
-m "Jonas Maurus <jonas@gopythongo.com>"
-d "python3 python3-pip python3-virtualenv virtualenv"
--deb-suggests "gnupg pbuilder aptly ruby ruby-dev"
--depends "python3 python-virtualenv python-pip virtualenv"
{{basedir}}
"""


class PbuilderFpmAptlyInitializer(BaseInitializer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def initializer_name(self) -> str:
        return "pbuilder_deb"

    def build_config(self) -> None:
        pass

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
