# =* encoding: utf-8 *-

from typing import Set, Any, Dict

from gopythongo.packers import BasePacker
from gopythongo.utils import GoPythonGoEnableSuper
from gopythongo.versioners.parsers import VersionContainer


class PackerArtifact(GoPythonGoEnableSuper):
    """
    Describes the results of a Packer.pack() call for other parts of the system that need to interact with it. For
    example: the aptly Store needs to store all the packages that the FPM Packer created.

      * The contents of ``artifact_metadata`` are entirely up to the Packer.
      * ``created_by`` is a reference to the Packer instance, in case it offers an API for Stores and other parts of the
        system to call.
    """
    def __init__(self, typedesignator: str, artifact_filename: str, artifact_metadata: Dict[str, str],
                 created_by: BasePacker, created_by_packername: str, *args: Any, **kwargs: Any) -> None:
        self.typedesignator = typedesignator
        self.artifact_filename = artifact_filename
        self.artifact_metadata = artifact_metadata,
        self.created_by = created_by
        self.created_by_packername = created_by_packername
        super().__init__(typedesignator, artifact_filename, artifact_metadata, created_by, *args, **kwargs)


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
        self.mounts = set()  # type: Set[str]
        self.packer_artifacts = set()  # type: Set[PackerArtifact]


the_context = BuildContext()  # type: BuildContext

__all__ = ["the_context", ]
