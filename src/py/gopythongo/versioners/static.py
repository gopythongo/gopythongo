# -* encoding: utf-8 *-

import gopythongo.versioners as _versioners


class StaticVersioner(_versioners.BaseVersioner):
    def __init__(self, *args, **kwargs):
        super(StaticVersioner, self).__init__(*args, **kwargs)

    @property
    def versioner_name(self):
        return u"static"

    @property
    def can_read(self):
        return False

    @property
    def can_create(self):
        return True

    def print_help(self):
        pass

    def add_args(self, parser):
        pass

    def validate_args(self, args):
        pass

    def create(self, args):
        pass


versioner_class = StaticVersioner
