# -* encoding: utf-8 *-

"""
tools to parse and compare Debian version strings as per
https://www.debian.org/doc/debian-policy/ch-controlfields.html. Partially based on
https://github.com/chaos/apt/blob/master/apt/apt-pkg/deb/debversion.cc (see debVersioningSystem::DoCmpVersion)
"""
from typing import List, TypeVar, Generic, Callable, Tuple, Union, Any

import re


class InvalidDebianVersionString(Exception):
    def __init__(self, msg, *args):
        message = "%s\nPlease see https://www.debian.org/doc/debian-policy/ch-controlfields.html for details." % msg
        self.args = ([message] + list(args)) if msg else args


def debian_substr_compare(a: str, b: str) -> int:
    """
    Compares two strings using Debian Policy Manual rules. This is complicated because standard Python str comparison
    works like this:

    >>> sorted(["~~", "~~a", "~", "", "a"], reverse=True)
    ['~~a', '~~', '~', 'a', '']

    However the Debian policy manual says version sorting should work like this:

    >>> debiansorted(["~~", "~~a", "~", "", "a"])
    ["~~", "~~a", "~", "", "a"]

    So it's just slightly different from inverted string sorting.

    :param a: a version string
    :type a: str
    :param b: a version string
    :type b: str
    :return: negative int if a<b; 0 if a==b; positive int if a>b
    """
    # '^' is our special character representing an "empty part" as '^' is not allowed in Debian version strings
    sortorder = "~^ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+-.:"

    def order(c: str) -> int:
        if c in sortorder:
            return sortorder.index(c)
        else:
            raise InvalidDebianVersionString("Cannot compare (%s, %s) because '%s' is not sortable" % (
                a, b, c
            ))

    def select_char(version_str: str, ix: int) -> str:
        if ix >= len(version_str):
            return '^'
        else:
            return version_str[ix]

    # numeric groups are handled separately from character groups
    a_is_numeric = re.match("[0-9]+", a)
    b_is_numeric = re.match("[0-9]+", b)
    if a_is_numeric and b_is_numeric:
        # DPM specifies to compare the numeric values for number groups
        a_int = int(a)
        b_int = int(b)
        return a_int - b_int
    elif a_is_numeric and not b_is_numeric:
        # ~ always sorts first, even before numbers, also shorter strings before longer strings (unless ~)
        if b.startswith("~") or b == "":
            return +1
        else:
            return -1
    elif not a_is_numeric and b_is_numeric:
        # ~ always sorts first, even before numbers, also shorter strings before longer strings (unless ~)
        if a.startswith("~") or a == "":
            return -1
        else:
            return +1
    else:
        maxlen = len(a) if len(a) > len(b) else len(b)
        for c_ix in range(0, maxlen):
            if order(select_char(a, c_ix)) < order(select_char(b, c_ix)):
                return -1
            if order(select_char(a, c_ix)) == order(select_char(b, c_ix)):
                continue
            if order(select_char(a, c_ix)) > order(select_char(b, c_ix)):
                return +1

    # the strings are equal
    return 0


def split_version_parts(version_str: str, version_char_re: str="[A-Za-z\+\.~]+") -> List[str]:
    """
    Splits ``version_str`` into groups of digits and characters to perform Debian-style version comparison.
    For example: "a67bhgs89" has 4 groups -> ["a", "67", "bhgs", "89"]
    :param version_str: the string to separate
    :type version_str: str
    :param version_char_re: a regular expression of valid characters in this version string as these can change (see DPM)
    :type version_char_re: str
    :return: a list of str
    :rtype: list
    """
    # re.split might return an empty string as the first element if version_str starts with a character
    if version_str:
        return [x for x in re.split("(%s)" % version_char_re, version_str) if x != ""]
    else:
        return [""]


def debian_versionpart_compare(mine: List[str], theirs: List[str]):
    maxlen = len(mine) if len(mine) > len(theirs) else len(theirs)
    for g_ix in range(0, maxlen):
        res = debian_substr_compare(mine[g_ix] if g_ix < len(mine) else "",
                                    theirs[g_ix] if g_ix < len(theirs) else "")
        if res != 0:
            return res

    if len(mine) == len(theirs):
        # equality achieved
        return 0

    # this shouldn't be reached
    raise Exception("Yo code... whatcha doing? This instruction should be unreachable.")


class DebianVersion(object):
    def __init__(self, epoch: str, version: str, revision: str) -> None:
        self.epoch = epoch  # type: str
        self.version = version  # type: str
        self.revision = revision  # type: str
        self.version_re = None  # type: str
        self.version_char_re = None  # type: str

        if self.epoch is not None:
            try:
                if int(self.epoch) == 0:
                    # special case: zero Epoch is no Epoch
                    self.epoch = None
            except ValueError:
                raise InvalidDebianVersionString("Epoch must be an integer")

        self.validate()

    def validate(self):
        """
        :raises InvalidDebianVersionString: if this DebianVersion object represents an invalid version
        """
        details = ""
        if self.epoch:
            if self.revision:
                self.version_re = "^[A-Za-z0-9\+\.~\:\-]+$"
                self.version_char_re = "[A-Za-z\+\.~\:\-]+"
            else:
                self.version_re = "^[A-Za-z0-9\+\.~\:]+$"
                self.version_char_re = "[A-Za-z\+\.~\:]+"
                details = "Version string has no Revision and may not contain hyphens (-)."
        else:
            if self.revision:
                self.version_re = "^[A-Za-z0-9\+\.~\-]+$"
                self.version_char_re = "[A-Za-z\+\.~\-]+"
                details = "Version string has no Epoch and may not contain colons (:)."
            else:
                self.version_re = "^[A-Za-z0-9\+\.~]+$"
                self.version_char_re = "[A-Za-z\+\.~]+"
                details = "Version string has neither Epoch nor Revision and may not contain colons (:) or hyphens (-)."

        if self.epoch:
            if not re.match("[0-9]+", self.epoch):
                raise InvalidDebianVersionString("Epoch error: %s does not match %s. %s" %
                                                 (self.epoch, "[0-9]+", details))
        if self.revision:
            if not re.match("[A-Za-z0-9\+\.~]+", self.revision):
                raise InvalidDebianVersionString("Revision error: %s does not match %s. %s" %
                                                 (self.revision, "[A-Za-z0-9\+\.~]+", details))
        if not re.match(self.version_re, self.version):
            raise InvalidDebianVersionString("Version error: %s does not match %s. %s" %
                                             (self.version, self.version_re, details))

    @classmethod
    def fromstring(cls: type, version_str: str) -> 'DebianVersion':
        epoch, version, revision = (None, None, None)
        if ":" in version_str:
            epoch = version_str.split(":")[0]
            version_str = version_str.split(":")[1]
        if "-" in version_str:
            revision = version_str.rsplit("-")[1]
            version_str = version_str.rsplit("-")[0]
        version = version_str
        return cls(epoch, version, revision)

    def __repr__(self) -> str:
        return "DebianVersion<Epoch:%s, Version:%s, Revision:%s, Validation Regex:%s, Split Regex: %s>" % (
            self.epoch, self.version, self.revision, self.version_re, self.version_char_re
        )

    def __str__(self) -> str:
        return "%s%s%s" % (
            ("%s:" % self.epoch) if self.epoch else "",
            self.version if self.version else "",
            ("-%s" % self.revision) if self.revision else "",
        )

    def tostring(self) -> str:
        return str(self)

    def __lt__(self, other: 'DebianVersion') -> bool:
        # special case: zero Epoch is the same as no Epoch
        if self.epoch is not None and other.epoch is not None and \
           int(self.epoch) != int(other.epoch) and int(self.epoch) != 0 and int(other.epoch) != 0:
            return int(self.epoch) < int(other.epoch)

        res = debian_versionpart_compare(split_version_parts(self.version, self.version_char_re),
                                         split_version_parts(other.version, self.version_char_re))

        if res == 0:
            return debian_versionpart_compare(split_version_parts(self.revision),
                                              split_version_parts(other.revision)) < 0
        else:
            return res < 0

    def __eq__(self, other: Union['DebianVersion', Any, None]) -> bool:
        return repr(self) == repr(other)

    def as_tuple(self) -> Tuple[str, str, str]:
        return self.epoch, self.version, self.revision
