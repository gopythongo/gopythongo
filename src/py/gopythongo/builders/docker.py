# -* encoding: utf-8 *-

import gopythongo.shared.docker_args

from gopythongo.utils import print_info, highlight

builder_name = u"docker"


def add_args(parser):
    gopythongo.shared.docker_args.add_shared_args(parser)


def validate_args(args):
    gopythongo.shared.docker_args.validate_shared_args(args)


def build(args):
    print_info("Building with %s" % highlight("docker"))
