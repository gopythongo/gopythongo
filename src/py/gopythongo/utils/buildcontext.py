# =* encoding: utf-8 *-


class BuildContext(object):
    """
    This is a global singleton accessed via ``gopythongo.utils.buildcontext.the_context`` that should be used
    (*sparingly*) to share global data between Builders, Assemblers, Versioners, Packers and Stores. Most importantly,
    the ``mounts`` attribute allows you to add file system paths which will be mounted into the build environment by
    the selected Builder.

        >>> from gopythongo.utils.buildcontext import the_context
        >>> the_context.mounts.add("path/to/my/stuff")  # makes your stuff available to your code during the build
    """
    def __init__(self):
        self.packs = []
        self.read_version = None
        self.out_version = None
        self.gopythongo_path = None
        self.gopythongo_cmd = None
        self.mounts = set()


the_context = BuildContext()

__all__ = [the_context, ]
