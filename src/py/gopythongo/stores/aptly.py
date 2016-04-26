# -* encoding: utf-8 *-


import gopythongo.shared.aptly_args

store_name = u"aptly"


def add_args(parser):
    gopythongo.shared.aptly_args.add_shared_args(parser)


def validate_args(args):
    return True


def store(args):
    pass
