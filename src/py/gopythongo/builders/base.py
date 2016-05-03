# -* encoding: utf-8 *-
from gopythongo.utils import GoPythonGoEnableSuper


class BaseBuilder(GoPythonGoEnableSuper):
    def __init__(self, *args, **kwargs):
        super(BaseBuilder, self).__init__(*args, **kwargs)
