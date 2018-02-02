#!/usr/bin/python
# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
import sys

from distutils.core import setup
from setuptools import find_packages

_package_root = "src/py"
_root_package = 'gopythongo'


with open("src/py/gopythongo/__init__.py", "rt", encoding="utf-8") as vf:
    lines = vf.readlines()

_version = "0.0.0+local"
for l in lines:
    m = re.match("version = \"(.*?)\"", l)
    if m:
        _version = m.group(1)

_packages = find_packages(_package_root, exclude=["*.tests", "*.tests.*", "tests.*", "tests"])

_requirements = [
    'Jinja2==2.10',
    'ConfigArgParse==0.12.0',
    'Sphinx==1.6.6',
    'sphinx-rtd-theme==0.2.4',
    'colorama==0.3.9',
    'semantic-version==2.6.0',
    'packaging==16.8',
    'typing==3.6.4',
    'hvac==0.4.0',
    'docker-py==1.10.6',
    'dockerpty==0.4.1',
    'pyopenssl==17.5.0',
    'bumpversion==0.5.3',
]

if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 3):
    _requirements.append('backports.shutil_get_terminal_size==1.0.0')

setup(
    name='gopythongo',
    version=_version,
    packages=_packages,
    package_dir={
        '': _package_root,
    },
    entry_points={
        "console_scripts": [
            "gopythongo = gopythongo.main:main",
            "vaultwrapper = gopythongo.vaultwrapper:main",
            "vaultgetcert = gopythongo.vaultgetcert:main",
        ]
    },
    install_requires=_requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Environment :: Console",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: POSIX",
    ],
    author="Jonas Maurus (@jdelic)",
    author_email="jonas@gopythongo.com",
    maintainer="GoPythonGo.com",
    maintainer_email="info@gopythongo.com",
    description="Build shippable virtualenvs",
)
