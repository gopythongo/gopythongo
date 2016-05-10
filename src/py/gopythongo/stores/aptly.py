# -* encoding: utf-8 *-

import gopythongo.shared.aptly_args as _aptly_args

from gopythongo.stores import BaseStore


class AptlyStore(BaseStore):
    def __init__(self, *args, **kwargs):
        super(AptlyStore, self).__init__(*args, **kwargs)

    @property
    def store_name(self):
        return u"aptly"

    def add_args(self, parser):
        _aptly_args.add_shared_args(parser)

    def validate_args(self, args):
        _aptly_args.validate_shared_args(args)

    def store(self, args):
        pass


store_class = AptlyStore
