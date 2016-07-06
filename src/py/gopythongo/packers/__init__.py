# -* encoding: utf-8 *-
import argparse

from typing import Dict, Any

from gopythongo.utils import plugins, CommandLinePlugin, ErrorMessage

packers = {}  # type: Dict[str, 'BasePacker']


def init_subsystem() -> None:
    global packers
    from gopythongo.packers import fpm, targz

    packers = {
        u"fpm": fpm.packer_class(),
        u"targz": targz.packer_class(),
    }

    plugins.load_plugins("gopythongo.packers", packers, "packer_class", BasePacker, "packer_name")


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

    def pack(self, args: argparse.Namespace) -> None:
        pass


def add_args(parser: argparse.ArgumentParser) -> None:
    for m in packers.values():
        m.add_args(parser)

    gr_packers = parser.add_argument_group("Packer shared options")
    gr_packers.add_argument("--copy-out", dest="copy_out", default=None,
                            help="The destination path inside the build environment, where the resulting packages will "
                                 "be copied. This will usually be the path of a bindmount, created with --mount in the "
                                 "build folder of your build server, for example.")


def validate_args(args: argparse.Namespace) -> None:
    if args.packer in packers.keys():
        packers[args.packer].validate_args(args)


def pack(args: argparse.Namespace) -> None:
    packers[args.packer].pack(args)
