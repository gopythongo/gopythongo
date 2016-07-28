# -* encoding: utf-8 *-
import configargparse
import os

from typing import Dict, List

from gopythongo.utils import ErrorMessage, highlight
from gopythongo.utils.buildcontext import the_context


_args_added = False
_args_validated = False


_dependencies = {
    "debian/jessie": ["python", "python-pip", "python-dev", "python3-dev", "python-virtualenv",
                      "virtualenv"]
}  # type: Dict[str, List[str]]


def get_dependencies() -> Dict[str, List[str]]:
    return _dependencies


def add_dependencies(key: str, deps: List[str]) -> None:
    global _dependencies
    _dependencies[key] = deps


def add_shared_args(parser: configargparse.ArgumentParser) -> None:
    global _args_added
    if _args_added:
        return
    else:
        _args_added = True

    gr_sb = parser.add_argument_group("Common Builder options")
    gr_sb.add_argument("--run-after-create", dest="run_after_create", action="append",
                       help="Specify commands (e.g. shell scripts) which will be run using inside a build environment "
                            "e.g. pbuilder or docker  after a build environment is created. This allows you to perform "
                            "additional necessary build configuration, which shouldn't be repeated for each subsequent "
                            "build (e.g. 'gem install fpm')")


def validate_shared_args(args: configargparse.Namespace) -> None:
    global _args_validated
    if _args_validated:
        return
    else:
        _args_validated = True

    if not args.is_inner:
        for runspec in args.run_after_create:
            if os.path.isfile(runspec):
                if not os.access(runspec, os.X_OK):
                    raise ErrorMessage("Pbuilder is supposed to run %s inside the build environment, but it's not "
                                       "executable" % highlight(runspec))
                the_context.mounts.add(os.path.abspath(os.path.dirname(runspec)))

