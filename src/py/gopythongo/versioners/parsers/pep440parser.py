# -* encoding: utf-8 *-
import configargparse

from copy import copy
from typing import Any, List, Tuple, Union, Type

from gopythongo.utils import highlight, ErrorMessage
from gopythongo.versioners.parsers import BaseVersionParser, VersionContainer
from packaging.version import parse, InvalidVersion, Version, _Version


class PEP440Adapter(Version):
    """
    provides some extra utility methods for GoPythonGo
    """
    def to_parts(self, *, epoch_suffix: str="!", release_sep: str=".", pre_prefix: str="", pre_sep: str="",
                 post_prefix: str=".", dev_prefix: str=".", local_prefix: str="+", local_sep: str=".") -> List[str]:
        parts = []  # type:List[str]

        # Epoch
        if self._version.epoch != 0:
            parts.append("{0}{1}".format(self._version.epoch, epoch_suffix))

        # Release segment
        parts.append(release_sep.join(str(x) for x in self._version.release))

        # Pre-release
        if self._version.pre is not None:
            parts.append("{1}{0}".format(pre_sep.join(str(x) for x in self._version.pre), pre_prefix))

        # Post-release
        if self._version.post is not None:
            parts.append("{1}post{0}".format(self._version.post[1], post_prefix))

        # Development release
        if self._version.dev is not None:
            parts.append("{1}dev{0}".format(self._version.dev[1], dev_prefix))

        # Local version segment
        if self._version.local is not None:
            parts.append(
                "{1}{0}".format(local_sep.join(str(x) for x in self._version.local), local_prefix)
            )

        return parts


def _adapt(v: Version) -> PEP440Adapter:
    return PEP440Adapter(str(v))


class PEP440VersionParser(BaseVersionParser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def versionparser_name(self) -> str:
        return "pep440"

    @property
    def supported_actions(self) -> List[str]:
        return ["bump-epoch", "bump-major", "bump-minor", "bump-patch",
                "bump-pre", "bump-dev", "bump-post"]

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        pass

    def validate_args(self, args: configargparse.Namespace) -> None:
        pass

    def parse(self, version_str: str, args: configargparse.Namespace) -> VersionContainer[PEP440Adapter]:
        try:
            version = _adapt(parse(version_str))
        except InvalidVersion as e:
            raise ErrorMessage("%s is not a valid PEP-440 version string: %s" %
                               (highlight(version_str), str(e))) from e

        return VersionContainer(version, self.versionparser_name)

    # mad hackz ahead
    def _patch_version(self, version: PEP440Adapter, *, epoch: int=None, release: Tuple[int, ...]=None,
                       pre: Tuple[str, int]=None, dev: Tuple[str, int]=None, post: Tuple[str, int]=None,
                       local: Tuple[Union[str, int], ...]=None) -> None:
        version._version = _Version(
            epoch=epoch if epoch else version._version.epoch,
            release=release if release else version._version.release,
            pre=pre if pre else version._version.pre,
            dev=dev if dev else version._version.dev,
            post=post if post else version._version.post,
            local=local if local else version._version.local,
        )

    def can_execute_action(self, version: VersionContainer, action: str) -> bool:
        v = version.version  # type: Version
        if action == "bump-pre" and v._version.post or v._version.dev:
            return False
        elif action == "bump-post" and v._version.dev or v._version.pre:
            return False
        elif action == "bump-dev" and v._version.pre or v._version.post:
            return False
        else:
            return True

    def execute_action(self, version: VersionContainer, action: str) -> VersionContainer:
        ver = copy(version.version)  # type: PEP440Adapter

        cmdindex = ["bump-major", "bump-minor", "bump-patch"]

        if action == "bump-epoch":
            self._patch_version(ver, epoch=ver._version.epoch + 1)
        elif action in cmdindex:
            ix = cmdindex.index(action)
            if ix < len(ver._version.release):
                rel = list(ver._version.release)
                rel[ix] += 1
                self._patch_version(ver, release=tuple(rel))
            else:
                raise ErrorMessage("--version-action is %s, but the version string %s does not have a %s field." %
                                   (highlight(action), highlight(str(ver)), highlight(action[5:])))
        elif action == "bump-pre":
            if ver._version.pre and isinstance(ver._version.pre[1], int):
                self._patch_version(ver, pre=(ver._version.pre[0], ver._version.pre[1] + 1))
            else:
                if ver._version.post or ver._version.dev:
                    raise ErrorMessage("--version-action is %s, but the version string %s already has a dev or post "
                                       "field." % (highlight(action), highlight(str(ver))))
                else:
                    self._patch_version(ver, pre=("a", 1))
        elif action == "bump-dev":
            if ver._version.dev and isinstance(ver._version.dev[1], int):
                self._patch_version(ver, dev=(ver._version.dev[0], ver._version.dev[1] + 1))
            else:
                if ver._version.pre or ver._version.post:
                    raise ErrorMessage("--version-action is %s, but the version string %s already has a pre or post "
                                       "field." % (highlight(action), highlight(str(ver))))
                else:
                    self._patch_version(ver, dev=("dev", 1))
        elif action == "bump-post":
            if ver._version.post and isinstance(ver._version.post[1], int):
                self._patch_version(ver, post=(ver._version.post[0], ver._version.post[1] + 1))
            else:
                if ver._version.pre or ver._version.dev:
                    raise ErrorMessage("--version-action is %s, but the version string %s already has a dev or pre "
                                       "field." % (highlight(action), highlight(str(ver))))
                else:
                    self._patch_version(ver, post=("post", 1))

        return VersionContainer(ver, self.versionparser_name)

    def deserialize(self, serialized: str) -> VersionContainer:
        return VersionContainer(parse(serialized), self.versionparser_name)

    def print_help(self) -> None:
        print("%s\n"
              "=====================\n"
              "\n"
              "The %s Version Parser should be used with PIP/PEP-440 version strings.\n"
              "This is by far the easiest choice if you're uploading your source code to the\n"
              "cheeseshop (pypi) or a local pypi installation through setup.py anyway, since\n"
              "that means that the version string used by your setup.py is probably already\n"
              "pep440-compatible anyway.\n"
              "\n"
              "The PEP440 Version Parser does not require any additional configuration.\n" %
              (highlight("PEP440 Version Parser"), highlight("pep440")))


versionparser_class = PEP440VersionParser  # type: Type[PEP440VersionParser]
