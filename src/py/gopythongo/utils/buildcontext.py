# =* encoding: utf-8 *-

from typing import Set
from gopythongo.versioners.parsers import VersionContainer


class BuildContext(object):
    """
    This is a global singleton accessed via ``gopythongo.utils.buildcontext.the_context`` that should be used
    (*sparingly*) to share global data between Builders, Assemblers, Versioners, Packers and Stores. Most importantly,
    the ``mounts`` attribute allows you to add file system paths which will be mounted into the build environment by
    the selected Builder.

        >>> from gopythongo.utils.buildcontext import the_context
        >>> the_context.mounts.add("path/to/my/stuff")  # makes your stuff available to your code during the build
    """
    def __init__(self) -> None:
        self.packs = []  # type: List[str]
        self.read_version = None  # type: VersionContainer
        self.out_version = None  # type: VersionContainer
        self.gopythongo_path = None  # type: str
        self.gopythongo_cmd = None  # type: List[str]
        self.mounts = set()  # type: Set


the_context = BuildContext()  # type: BuildContext

__all__ = ["the_context", ]
