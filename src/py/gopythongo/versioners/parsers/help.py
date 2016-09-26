# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import configargparse

from typing import Any, Iterable, Union, Sequence, cast

from gopythongo.utils import highlight


class VersionParserHelpAction(configargparse.Action):
    def __init__(self,
                 option_strings: Sequence[str],
                 dest: str,
                 default: Any=None,
                 choices: Iterable[Any]=None,
                 help: str="Get help for GoPythonGo Version Parsers which take a version string read by a Versioner "
                           "and parse it or convert between version formats.") -> None:
        super().__init__(option_strings=option_strings, dest=dest, default=default,
                         nargs="?", choices=choices, help=help)

    def __call__(self, parser: configargparse.ArgumentParser, namespace: configargparse.Namespace,
                 values: Union[str, Sequence[Any], None], option_string: str=None) -> None:
        from gopythongo.versioners import get_version_parsers
        version_parsers = get_version_parsers()
        if values in version_parsers.keys():
            version_parsers[cast(str, values)].print_help()
        else:
            print("Version Parsers\n"
                  "===============\n"
                  "\n"
                  "Version Parsers take a version string read by a Versioner in one format and\n"
                  "convert it into a transformable object. Most versioning systems are\n"
                  "incompatible with each other (e.g. SemVer 2.0.0 and PEP-440). But for some a\n"
                  "lossless transformation can be defined. Version Parsers can tell GoPythonGo\n"
                  "when they are able to convert losslessly between from another versioning\n"
                  "system. Most built-in Version Parsers can, for example, transform SemVer\n"
                  "conformant version strings into their format without loss of information.\n"
                  "\n"
                  "Built-in Version Parsers\n"
                  "------------------------\n"
                  "\n"
                  "GoPythonGo has a number of built-in version parsers which you can use to\n"
                  "process version strings read by a Versioner:\n"
                  "\n"
                  "    %s - parses Debian version strings as described in the Debian Policy\n"
                  "             Manual https://www.debian.org/doc/debian-policy/\n"
                  "\n"
                  "    %s - parses SemVer version strings adhering fo the format defined by\n"
                  "             http://semver.org/\n"
                  "\n"
                  "    %s  - allows you to define a regular expression with named groups based\n"
                  "             on SemVer to easily read arbitrary version strings. Internally\n"
                  "             those are treated like SemVer versions after matching the\n"
                  "             regular expression.\n"
                  "\n"
                  "Use %s\n"
                  "to learn more about the available Version Parsers.\n"
                  "\n"
                  "You can find information on writing and plugging your own Version Parsers into\n"
                  "GoPythonGo on http://gopythongo.com/.\n" %
                  (highlight("debian"), highlight("semver"), highlight("regex"),
                   highlight("--help-versionparser=[%s]" % ", ".join(version_parsers.keys()))))

        parser.exit()
