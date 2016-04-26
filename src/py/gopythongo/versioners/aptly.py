# -* encoding: utf-8 *-

import gopythongo.shared.aptly_args


versioner_name = u"aptly"


def add_args(parser):
    gopythongo.shared.aptly_args.add_shared_args(parser)


def validate_args(args):
    gopythongo.shared.aptly_args.validate_shared_args(args)


def validate_param(param):
    pass


def read(readspec, parsespec):
    pass


def create(createspec, action):
    pass


def print_help():
    pass
