# -* encoding: utf-8 *-


import gopythongo.shared.aptly_args
from gopythongo.stores import BaseStore


class AptlyStore(BaseStore):
    def __init__(self, *args, **kwargs):
        super(AptlyStore, self).__init__(*args, **kwargs)

    @property
    def store_name(self):
        return u"aptly"

    def add_args(self, parser):
        gopythongo.shared.aptly_args.add_shared_args(parser)

    def validate_args(self, args):
        return True

    def store(self, args):
        pass


store_class = AptlyStore
