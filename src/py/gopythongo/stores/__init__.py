# -* encoding: utf-8 *-

import sys

from gopythongo.utils import print_error, plugins, CommandLinePlugin

stores = None


def init_subsystem():
    global stores

    from gopythongo.stores import aptly, docker
    stores = {
        u"aptly": aptly.store_class(),
        u"docker": docker.store_class(),
    }

    try:
        plugins.load_plugins("gopythongo.stores", stores, "store_class", BaseStore, "store_name")
    except ImportError as e:
        print_error(str(e))
        sys.exit(1)


class BaseStore(CommandLinePlugin):
    def __init__(self, *args, **kwargs):
        super(BaseStore, self).__init__(*args, **kwargs)

    @property
    def store_name(self):
        """
        Return the identifier and command-line parameter value for --store used by this Store.
        :returns: the identifier
        :rtype: str
        """
        raise NotImplementedError("Each subclass of BaseStore MUST implement store_name")

    def store(self, args):
        pass


def add_args(parser):
    global stores

    for s in stores.values():
        s.add_args(parser)


def validate_args(args):
    for s in stores.values():
        s.validate_args(args)


def store(args):
    pass
