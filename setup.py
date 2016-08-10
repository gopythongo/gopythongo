#!/usr/bin/python
# -* encoding: utf-8 *-
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
    'Jinja2==2.8',
    'ConfigArgParse==0.9.3',
    'Sphinx==1.3.1',
    'sphinx-rtd-theme==0.1.9',
    'colorama==0.3.7',
    'semantic_version==2.5.0',
    'packaging==16.6',
    'typing==3.5.2.2',
    'hvac==0.2.15',
    'docker-py==1.9.0',
    'dockerpty==0.4.1',
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
            "gpg_vault_wrapper = gopythongo.gpg_vault_wrapper:main"
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
