# -* encoding: utf-8 *-

import sys

from gopythongo.utils import print_error, plugins, CommandLinePlugin

packers = None


def init_subsystem():
    global packers
    from gopythongo.packers import fpm, targz
    packers = {
        u"fpm": fpm.packer_class(),
        u"targz": targz.packer_class(),
    }
    try:
        plugins.load_plugins("gopythongo.packers", packers, "packer_class", BasePacker, "packer_name")
    except ImportError as e:
        print_error(str(e))
        sys.exit(1)


class BasePacker(CommandLinePlugin):
    def __init__(self, *args, **kwargs):
        super(BasePacker, self).__init__(*args, **kwargs)

    @property
    def packer_name(self):
        """
        Return the identifier and command-line parameter value for --packer used by this Packer.
        :returns: the identifier
        :rtype: str
        """
        raise NotImplementedError("Each subclass of BasePacker MUST implement packer_name")

    def pack(self, args):
        pass


def add_args(parser):
    for m in packers.values():
        m.add_args(parser)

    gr_packers = parser.add_argument_group("Packer shared options")
    gr_packers.add_argument("--copy-out", dest="copy_out", default=None,
                            help="The destination path inside the build environment, where the resulting packages will "
                                 "be copied. This will usually be the path of a bindmount, created with --mount in the "
                                 "build folder of your build server, for example.")


def validate_args(args):
    if args.packer in packers.keys():
        packers[args.packer].validate_args(args)


def pack(args):
    packers[args.packer].pack(args)
