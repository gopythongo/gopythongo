# =* encoding: utf-8 *-


class BuildContext(object):
    def __init__(self):
        self.packs = []
        self.read_version = None
        self.out_version = None
        self.gopythongo_path = None
        self.gopythongo_cmd = None

the_context = BuildContext()

__all__ = [the_context,]
