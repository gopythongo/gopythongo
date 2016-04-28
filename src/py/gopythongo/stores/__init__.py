# -* encoding: utf-8 *-

import sys

from gopythongo.utils import print_error, plugins
from gopythongo.stores import aptly, docker


stores = {
    u"aptly": aptly,
    u"docker": docker,
}


def add_args(parser):
    global stores

    try:
        plugins.load_plugins("gopythongo.stores", stores, "store_name", ["add_args", "validate_args", "store"])
    except ImportError as e:
        print_error(str(e))
        sys.exit(1)

    for s in stores.values():
        s.add_args(parser)


def validate_args(args):
    for s in stores:
        s.validate_args(args)


def store(args):
    pass
