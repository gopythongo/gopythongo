# -* encoding: utf-8 *-
from typing import Sequence, Any, Iterable, Union, cast

import configargparse


class AssemblerHelpAction(configargparse.Action):
    def __init__(self,
                 option_strings: Sequence[str],
                 dest: str,
                 default: Any=None,
                 choices: Iterable[Any]=None,
                 help: str="Get help on Assemblers that put together your application.") -> None:
        super().__init__(option_strings=option_strings, dest=dest, default=default,
                         nargs="?", choices=choices, help=help)

    def __call__(self, parser: configargparse.ArgumentParser, namespace: configargparse.Namespace,
                 values: Union[str, Sequence[Any], None], option_string: str=None) -> None:
        from gopythongo.assemblers import get_assemblers
        assemblers = get_assemblers()
        if values in assemblers.keys():
            assemblers[cast(str, values)].print_help()
        else:
            print("Assemblers\n"
                  "==========\n"
                  "\n")

        parser.exit(0)
