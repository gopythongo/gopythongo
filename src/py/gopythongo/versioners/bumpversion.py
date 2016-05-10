# -* encoding: utf-8 *-

import sys
import os

from gopythongo.utils import print_error, highlight
from gopythongo.versioners import BaseVersioner


class BumpVersioner(BaseVersioner):
    def __init__(self, *args, **kwargs):
        super(BumpVersioner, self).__init__(*args, **kwargs)

    @property
    def versioner_name(self):
        return u"bumpversion"

    def add_args(self, parser):
        gr_bv = parser.add_argument_group("Bumpversion options")
        gr_bv.add_argument("--use-bumpversion", dest="bumpversion_executable", default=None,
                           help="Set the path to the bumpversion shells script. Required if you want to use the "
                                "bumpversion Versioner.")

    def validate_args(self, args):
        if not args.bumpversion_executable:
            print_error("To use the bumpversion Versioner, you must set %s" % highlight("--use-bumpversioner"))
            sys.exit(1)

        if not os.path.exists(args.bumpversion_executable) or not os.access(args.bumpversion_executable, os.X_OK):
            print_error("%s (from %s) does not exist or is not executable" %
                        (highlight(args.bumpversion_executable), highlight("--use-bumpversioner")))
            sys.exit(1)

    @property
    def can_read(self):
        return True

    @property
    def can_create(self):
        return True

    def read(self, args):
        pass

    def create(self, args):
        pass


versioner_class = BumpVersioner
