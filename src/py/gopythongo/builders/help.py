# -* encoding: utf-8 *-
import configargparse
from typing import Sequence, Union, Any, cast, Iterable


class BuilderHelpAction(configargparse.Action):
    def __init__(self,
                 option_strings: Sequence[str],
                 dest: str,
                 default: Any=None,
                 choices: Iterable[Any]=None,
                 help: str="Show help for GoPythonGo Builders.") -> None:
        super().__init__(option_strings=option_strings, dest=dest, default=default,
                         nargs="?", choices=choices, help=help)

    def __call__(self, parser: configargparse.ArgumentParser, namespace: configargparse.Namespace,
                 values: Union[str, Sequence[Any], None], option_string: str=None) -> None:
        from gopythongo.builders import get_builders
        builders = get_builders()
        if values in builders.keys():
            builders[cast(str, values)].print_help()
        else:
            print("Builders\n"
                  "========\n"
                  "\n")

        parser.exit(0)
