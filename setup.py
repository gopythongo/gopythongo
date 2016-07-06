#!/usr/bin/python
# -* encoding: utf-8 *-

import sys

from distutils.core import setup
from setuptools import find_packages

_package_root = "src/py"
_root_package = 'gopythongo'

import time  # noqa
_version = "1.0.dev%s" % int(time.time())
_packages = find_packages(_package_root, exclude=["*.tests", "*.tests.*", "tests.*", "tests"])

_requirements = [
    'Jinja2==2.8',
    'ConfigArgParse==0.9.3',
    'Sphinx==1.3.1',
    'sphinx-rtd-theme==0.1.9',
    'colorama==0.3.7',
    'semantic_version==2.5.0',
    'packaging==16.6',
]

if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 3):
    _requirements.append('backports.shutil_get_terminal_size==1.0.0')

if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 5):
    _requirements.append('typing==3.5.2.2')

setup(
    name='gopythongo',
    version=_version,
    packages=_packages,
    package_dir={
        '': _package_root,
    },
    entry_points = {
        "console_scripts": [
            "gopythongo = gopythongo.main:main"
        ]
    },
    install_requires=_requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Environment :: Console",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX",
    ],
    author="Jonas Maurus (@jdelic)",
    author_email="jonas@gopythongo.com",
    maintainer="GoPythonGo.com",
    maintainer_email="info@gopythongo.com",
    description="Build shippable virtualenvs",
)
