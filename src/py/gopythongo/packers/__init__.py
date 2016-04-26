# -* encoding: utf-8 *-

import sys

from gopythongo.utils import print_error, plugins
from gopythongo.packers import fpm, targz

packers = {
    "fpm": fpm,
    "targz": targz,
}


def add_args(parser):
    global packers

    try:
        plugins.load_plugins("gopythongo.packers", packers, "packer_name", ["add_args", "validate_args", "pack"])
    except ImportError as e:
        print_error(e.message)
        sys.exit(1)

    for m in packers.values():
        m.add_args(parser)


def validate_args(args):
    for m in packers.values():
        m.validate_args(args)


def pack(args):
    pass
