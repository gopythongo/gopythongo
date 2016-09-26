# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from typing import Sequence, Any, Iterable, Union, cast

import configargparse


class PackerHelpAction(configargparse.Action):
    def __init__(self,
                 option_strings: Sequence[str],
                 dest: str,
                 default: Any=None,
                 choices: Iterable[Any]=None,
                 help: str="Get help on Packers that pack up your application for delivery to a Store.") -> None:
        super().__init__(option_strings=option_strings, dest=dest, default=default,
                         nargs="?", choices=choices, help=help)

    def __call__(self, parser: configargparse.ArgumentParser, namespace: configargparse.Namespace,
                 values: Union[str, Sequence[Any], None], option_string: str=None) -> None:
        from gopythongo.packers import get_packers
        packers = get_packers()
        if values in packers.keys():
            packers[cast(str, values)].print_help()
        else:
            print("Packers\n"
                  "=======\n"
                  "\n")

        parser.exit(0)
