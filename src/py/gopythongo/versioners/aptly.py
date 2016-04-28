# -* encoding: utf-8 *-

import sys
import gopythongo.shared.aptly_args

from gopythongo.utils.debversion import DebianVersion, InvalidDebianVersionString
from gopythongo.utils import highlight, print_error

versioner_name = u"aptly"


def add_args(parser):
    gopythongo.shared.aptly_args.add_shared_args(parser)

    gr_aptly = parser.add_argument_group("Aptly Versioner")
    gr_aptly.add_argument("--fallback-version", dest="aptly_fallback_version", default=None,
                          help="If the APT repository does not yet contain a package with the name specified by "
                               "--package-name, the Aptly versioner can return a fallback value. This is useful for "
                               "fresh repositories.")


def validate_args(args):
    gopythongo.shared.aptly_args.validate_shared_args(args)

    if args.aptly_fallback_version:
        try:
            DebianVersion.fromstring(args.aptly_fallback_version)
        except InvalidDebianVersionString as e:
            print_error("The fallback version string you specified via %s is not a valid Debian version string. (%s)" %
                        (highlight("--fallback-version"), str(e)))
            sys.exit(1)


def validate_param(param):
    pass


def read(readspec, parsespec):
    pass


def create(createspec, action):
    pass


def print_help():
    pass
