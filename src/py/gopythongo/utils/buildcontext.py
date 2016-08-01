# =* encoding: utf-8 *-
import json
import os
import sys

import tempfile

from typing import Set, Any, Dict, List, Union, cast, Tuple
from typing.io import TextIO

from gopythongo.packers import BasePacker, get_packers
from gopythongo.utils import GoPythonGoEnableSuper, print_debug, highlight
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
        self.typedesignator = typedesignator  # type: str
        self.artifact_filename = artifact_filename  # type: str
        self.artifact_metadata = artifact_metadata  # type: Dict[str, str]
        self.created_by = created_by  # type: BasePacker
        self.created_by_packername = created_by_packername  # type: str
        super().__init__(typedesignator, artifact_filename, artifact_metadata, created_by, *args, **kwargs)

    def todict(self) -> Dict[str, Union[Dict[str, str], str]]:
        return {
            "t": self.typedesignator,
            "af": self.artifact_filename,
            "am": self.artifact_metadata,
            "cbp": self.created_by_packername,
        }

    @staticmethod
    def fromdict(dic: Dict[str, Union[str, Dict[str, str]]]) -> 'PackerArtifact':
        bp = get_packers()[cast(str, dic["cbp"])]
        return PackerArtifact(
            cast(str, dic["t"]), cast(str, dic["af"]), cast(Dict[str, str], dic["am"]), bp, cast(str, dic["cbp"])
        )


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
        self.packer_artifacts = set()  # type: Set[PackerArtifact]
        self.read_version = None  # type: VersionContainer[Any]
        self.generated_versions = None  # type: Dict[str, VersionContainer[Any]]
        self.gopythongo_path = None  # type: str
        self.gopythongo_cmd = None  # type: List[str]
        self.mounts = set()  # type: Set[str]
        # the tempmount can be used to create temporary files to pass to the inner GoPythonGo
        self.tempmount = tempfile.mkdtemp(prefix="gopythongo-")  # type: str
        fd, self.state_file = tempfile.mkstemp(dir=self.tempmount, text=True)  # type: Tuple[int, str]
        os.close(fd)
        self.mounts.add(self.tempmount)

    def write(self, outf: TextIO) -> None:
        json.dump({
            "read_version": self.read_version.todict(),
            "generated_versions": {key: value.todict() for key, value in self.generated_versions.items()},
            "packer_artifacts": [value.todict() for value in self.packer_artifacts],
            "tempmount": self.tempmount,
            "state_file": self.state_file
        }, outf)

    def parse_state(self, statestr: str) -> None:
        from gopythongo.versioners.parsers import VersionContainer
        state = json.loads(statestr)
        self.read_version = VersionContainer.fromdict(state["read_version"])
        self.generated_versions = {key: VersionContainer.fromdict(value)
                                   for key, value in state["generated_versions"].items()}
        self.packer_artifacts = set([PackerArtifact.fromdict(value) for value in state["packer_artifacts"]])
        self.tempmount = state["tempmount"]
        self.state_file = state["state_file"]

    def read(self, filename: str) -> None:
        with open(filename, "rt", encoding="utf-8") as f:
            state = f.read()
        self.parse_state(state)

    def save_state(self) -> None:
        with open(self.state_file, "wt", encoding="utf-8") as f:
            self.write(f)

    def load_state(self) -> None:
        print_debug("Reading state from %s in outer shell" % highlight(the_context.state_file))
        self.read(self.state_file)

    def get_gopythongo_inner_commandline(self, *, cwd: str=None) -> List[str]:
        cmd = self.gopythongo_cmd + ["--inner"] + ['--read-state="%s"' % self.state_file]
        cmd += ['--cwd="%s"' % cwd if cwd else os.getcwd()]
        cmd += sys.argv[1:]
        return cmd


the_context = BuildContext()  # type: BuildContext

__all__ = ["the_context", ]
