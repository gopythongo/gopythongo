# -* encoding: utf-8 *-
import configargparse
import os

from gopythongo.utils import ErrorMessage, highlight
from gopythongo.utils.buildcontext import the_context


_args_added = False
_args_validated = False


def add_args(parser: configargparse.ArgumentParser) -> None:
    global _args_added
    if _args_added:
        return
    else:
        _args_added = True

    gr_sb = parser.add_argument_group("Common Builder options")
    gr_sb.add_argument("--no-install-defaults", dest="install_defaults", action="store_false",
                       default=True,
                       help="By default GoPythonGo will always install python, python-virtualenv, python-pip, "
                            "python[3]-dev, virtualenv and possibly eatmydata. If you set this flag you will have to "
                            "install python using --apt-get, or GoPythonGo will not be able to run inside the "
                            "container, but this gives you more control about what Python version runs.")
    gr_sb.add_argument("--run-after-create", dest="run_after_create", action="append",
                       help="Specify commands (e.g. shell scripts) which will be run using inside a build environment "
                            "e.g. pbuilder or docker  after a build environment is created. This allows you to perform "
                            "additional necessary build configuration, which shouldn't be repeated for each subsequent "
                            "build (e.g. 'gem install fpm')")
    gr_sb.add_argument("--apt-get", dest="build_deps", action="append", default=[],
                       help="Packages to install using apt-get prior to creating the virtualenv (e.g. driver libs for "
                            "databases so that Python C extensions compile correctly")


def validate_args(args: configargparse.Namespace) -> None:
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

