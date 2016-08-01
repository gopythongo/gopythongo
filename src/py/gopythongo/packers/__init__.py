# -* encoding: utf-8 *-
import configargparse

from typing import Dict, Any, List, Union

from gopythongo.utils import plugins, CommandLinePlugin

_packers = {}  # type: Dict[str, 'BasePacker']


def get_packers() -> Dict[str, 'BasePacker']:
    return _packers


def init_subsystem() -> None:
    global _packers
    from gopythongo.packers import fpm, targz

    _packers = {
        u"fpm": fpm.packer_class(),
        u"targz": targz.packer_class(),
    }

    plugins.load_plugins("gopythongo.packers", _packers, "packer_class", BasePacker, "packer_name")


class BasePacker(CommandLinePlugin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def packer_name(self) -> str:
        """
        **@property**

        Return the identifier and command-line parameter value for --packer used by this Packer.
        :returns: the identifier
        :rtype: str
        """
        raise NotImplementedError("Each subclass of BasePacker MUST implement packer_name")

    @property
    def provides(self) -> List[str]:
        """
        **@property**

        return a list of output formats this Packer produces allowing a Store implementation to check whether it can
        handle the output of this Packer
        :return: a list of format specifiers (lowercased), for example: package formats like "rpm", "deb" or "docker"
        """
        raise NotImplementedError("Each subclass of BasePacker MUST implement provides")

    def pack(self, args: configargparse.Namespace) -> None:
        pass

    def predict_future_artifacts(self, args: configargparse.Namespace) -> Union[List[str], None]:
        """
        This method provides an internal API that is supposed to allow Store implementations to query a packer for
        a prediction of what it will provide during the build phase so that the Store implementation can query version
        information to process Versioner input and in its turn provide the Packer with a future-proof version string.

        For packaging systems like RPM/yum and DEB/apt this method should return a list of package names which will be
        created during the build phase so that reprorepo/aptly can query for existing versions of those package names
        in their package repositories.

        This method may return ``None`` if the Packer can't reasonably predict the future (for example for Docker
        hashes).
        :param args: command-line parameters given
        :return: A list of Packer-specific artifact identifiers (e.g. like package names) or ``None``
        """
        return None


def add_args(parser: configargparse.ArgumentParser) -> None:
    for m in _packers.values():
        m.add_args(parser)

    gr_packers = parser.add_argument_group("Packer shared options")
    gr_packers.add_argument("--copy-out", dest="copy_out", default=None,
                            help="The destination path inside the build environment, where the resulting packages will "
                                 "be copied. This will usually be the path of a bindmount, created with --mount in the "
                                 "build folder of your build server, for example.")


def validate_args(args: configargparse.Namespace) -> None:
    if args.packer in _packers.keys():
        _packers[args.packer].validate_args(args)


def pack(args: configargparse.Namespace) -> None:
    _packers[args.packer].pack(args)
