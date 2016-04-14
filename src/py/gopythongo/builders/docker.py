# -* encoding: utf-8 *-

import gopythongo.shared.docker_args

from gopythongo.utils import print_info, highlight_color, color_reset


def add_args(parser):
    gopythongo.shared.docker_args.add_shared_args(parser)


def validate_args(args):
    pass


def build(args):
    print_info("Building with %sdocker%s" % (highlight_color, color_reset))
