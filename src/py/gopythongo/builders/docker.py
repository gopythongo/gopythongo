# -* encoding: utf-8 *-

import gopythongo.shared.docker_args


def add_args(parser):
    gopythongo.shared.docker_args.add_shared_args(parser)


def validate_args():
    pass
