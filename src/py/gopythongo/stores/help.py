# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from typing import Sequence, Any, Iterable, Union, cast

import configargparse


class StoreHelpAction(configargparse.Action):
    def __init__(self,
                 option_strings: Sequence[str],
                 dest: str,
                 default: Any=None,
                 choices: Iterable[Any]=None,
                 help: str="Get help on Stores that store your application for deployment.") -> None:
        super().__init__(option_strings=option_strings, dest=dest, default=default,
                         nargs="?", choices=choices, help=help)

    def __call__(self, parser: configargparse.ArgumentParser, namespace: configargparse.Namespace,
                 values: Union[str, Sequence[Any], None], option_string: str=None) -> None:
        from gopythongo.stores import get_stores
        stores = get_stores()
        if values in stores.keys():
            stores[cast(str, values)].print_help()
        else:
            print("Stores\n"
                  "======\n"
                  "\n")

        parser.exit(0)
