#!/usr/bin/python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import re
import sys

from setuptools import setup, find_packages

try:
    from pip._internal.req import parse_requirements
except ImportError:
    from pip.req import parse_requirements

try:
    from pip._internal.download import PipSession
except ImportError:
    try:
        from pip.download import PipSession
    except ImportError:
        from pip._internal.network.session import PipSession


_package_root = "src/py"
_root_package = 'gopythongo'
_HERE = os.path.abspath(os.path.dirname(__file__))

with open("src/py/gopythongo/__init__.py", "rt", encoding="utf-8") as vf:
    lines = vf.readlines()

_version = "0.0.0+local"
for l in lines:
    m = re.match("version = \"(.*?)\"", l)
    if m:
        _version = m.group(1)

_packages = find_packages(_package_root, exclude=["*.tests", "*.tests.*", "tests.*", "tests"])

pipsession = PipSession()
reqs_generator = parse_requirements(os.path.join(_HERE, "requirements.txt"),
                                    session=pipsession)  # prepend setup.py's path (make no assumptions about cwd)
_requirements = [(str(r.requirement) if hasattr(r, 'requirement') else str(r.req)) for r in reqs_generator]

if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 3):
    _requirements.append('backports.shutil_get_terminal_size==1.0.0')

try:
    long_description = open(os.path.join(_HERE, 'README.md')).read()
except IOError:
    long_description = None

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
    long_description=long_description,
)
