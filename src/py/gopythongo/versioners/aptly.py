# -* encoding: utf-8 *-

import gopythongo.shared.aptly_args


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


def validate_param(param):
    pass


def read(readspec, parsespec):
    pass


def create(createspec, action):
    pass


def print_help():
    pass
