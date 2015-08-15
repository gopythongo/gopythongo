# -* coding: utf-8 *-

# Type stub for buildhelpers.debian so we're Python2 compatible
from typing import Tuple, List


def debian_substr_compare(a: str, b: str) -> int:
    pass


def split_version_parts(version_str: str, version_re: str) -> List[str]:
    pass


class DebianVersion(object):
    def __init__(self, epoch: str, version: str, revision: str):
        pass

    @staticmethod
    def fromstring(version_str: str) -> DebianVersion:
        pass

    def as_tuple(self) -> Tuple[str, str, str]:
        pass

    def __lt__(self, other: DebianVersion) -> bool:
        pass

    def __eq__(self, other: DebianVersion) -> bool:
        pass
