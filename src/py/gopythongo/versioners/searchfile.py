# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import re

import configargparse

from typing import Any, Type

from gopythongo.utils import highlight, ErrorMessage
from gopythongo.versioners import BaseVersioner


class SearchFileVersioner(BaseVersioner):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versioner_name(self) -> str:
        return u"searchfile"

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        gp_search = parser.add_argument_group("Search File Versioner options")
        gp_search.add_argument("--search-version-in", dest="search_version_in", default=None,
                               help="The file to read to find the version string.")
        gp_search.add_argument("--search-version-regex", dest="search_version_regex",
                               default="([0-9]+\.[0-9]+\.[0-9]+\.?(dev|rc|pre|post)?)",
                               help="Define the regular expression that we search for. The first match wins.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        if args.search_version_in:
            if not os.path.exists(args.search_version_in) or not os.access(args.search_version_in, os.R_OK):
                raise ErrorMessage("Can't read %s to search for version string" % highlight(args.search_version_in))
        else:
            raise ErrorMessage("Search file versioner requires %s" % highlight("--search-version-in"))


    @property
    def can_read(self) -> bool:
        return True

    def read(self, args: configargparse.Namespace) -> str:
        with open(args.search_version_in, mode="rt", encoding="utf-8") as rf:
            lines = rf.readlines()

        rx = re.compile(args.search_version_regex)
        for l in lines:
            m = rx.search(l)
            if m:
                return m.group(1)

        raise ErrorMessage("Unable to find a matching version string for regex %s in file %s" %
                           (highlight(args.search_version_regex), highlight(args.search_version_in)))

    def print_help(self) -> None:
        print("Search File Versioner\n"
              "=====================\n"
              "\n"
              "This versioner reads a whole file (be careful with big files) and searches it\n"
              "for a string matching the specified regular expression.\n")


versioner_class = SearchFileVersioner  # type: Type[SearchFileVersioner]

