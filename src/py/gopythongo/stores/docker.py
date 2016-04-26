# -* encoding: utf-8 *-

import gopythongo.shared.docker_args

store_name = u"docker"


def add_args(parser):
    gopythongo.shared.docker_args.add_shared_args(parser)


def validate_args(args):
    return True


def store(args):
    pass
