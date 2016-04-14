# -* encoding: utf-8 *-


_aptly_shared_args_added = False


def add_shared_args(parser):
    global _aptly_shared_args_added

    if not _aptly_shared_args_added:
        gr_aptly_shared = parser.add_argument_group("Aptly common parameters")
        gr_aptly_shared.add_argument("--use-aptly", dest="use_aptly", default="/usr/bin/aptly",
                                     help="The full path to the aptly executable to use")
        gr_aptly_shared.add_argument("--aptly-config", dest="aptly_config", default=None,
                                     help="Path to the aptly config file to use")
        gr_aptly_shared.add_argument("--repo", dest="repo", default=None,
                                     help="Name of the aptly repository to place the package in. (This must be "
                                          "accessible from the builder environment to be useful.)")

    _aptly_shared_args_added = True
