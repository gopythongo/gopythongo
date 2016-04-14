# -* encoding: utf-8 *-

import gopythongo.shared.aptly_args


def add_args(parser):
    gopythongo.shared.aptly_args.add_shared_args(parser)

    gr_aptly = parser.add_argument_group("Aptly versioner parameters")

