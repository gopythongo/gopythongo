# -* encoding: utf-8 *-

from gopythongo.packers import fpm, targz


def add_args(parser):
    for m in [fpm, targz]:
        m.add_args(parser)


def validate_args(args):
    for m in [fpm, targz]:
        m.validate_args(args)
