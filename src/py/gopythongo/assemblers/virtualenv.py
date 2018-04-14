# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import configargparse
import os

from typing import Type

from gopythongo.assemblers import BaseAssembler
from gopythongo.utils import ErrorMessage, highlight, run_process, print_info, create_script_path


class VirtualEnvAssembler(BaseAssembler):
    @property
    def assembler_name(self) -> str:
        return "virtualenv"

    @property
    def assembler_type(self) -> str:
        return BaseAssembler.TYPE_ISOLATED

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        gr_pip = parser.add_argument_group("PIP Assembler options")
        gr_pip.add_argument("--pip-opts", dest="pip_opts", action="append", default=[], env_var="PIP_OPTS",
                            help="Any string specified here will be directly appended to all pip command-lines when it "
                                 "is invoked, allowing you to specify arbitrary extra command-line parameters, like "
                                 "--extra-index. Make sure that you use an equals sign, i.e. --pip-opts='' to avoid "
                                 "'Unknown parameter' errors! http://bugs.python.org/issue9334")
        gr_pip.add_argument("--upgrade-pip", dest="upgrade_pip", action="store_true", default=False,
                            help="If specified, GoPythonGo will update pip and virtualenv inside the build environment "
                                 "to the newest available version before installing packages")

        gr_setuppy = parser.add_argument_group("Setup.py Assembler options")
        gr_setuppy.add_argument("--setuppy-install", dest="setuppy_install", action="append", default=[],
                                help="After all pip commands have run, this can run 'python setup.py install' on " +
                                     "additional packages available in any filesystem path. This option can be " +
                                     "used multiple times")

        gr_python = parser.add_argument_group("Python ecosystem options")
        gr_python.add_argument("--use-virtualenv", dest="virtualenv_binary", default="/usr/bin/virtualenv",
                               env_var="VIRTUALENV_EXECUTABLE",
                               help="Set an alternative virtualenv binary to use inside the builder container")
        gr_python.add_argument("--python-binary", dest="python_binary", default="python3",
                               help="Force virtualenv to use a certain Python version (Default: 'python3'). This will "
                                    "be passed to virtualenv's -p parameter. You must change this if you want to build "
                                    "and ship Python 2.x virtual environments.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        for path in args.setuppy_install:
            if not (os.path.exists(path) and os.path.exists(os.path.join(path, "setup.py"))):
                raise ErrorMessage("Cannot run setup.py in %s, because it does not exist" % highlight(path))

        if not os.path.exists(args.virtualenv_binary) or not os.access(args.virtualenv_binary, os.X_OK):
            raise ErrorMessage("virtualenv not found in path or not executable (%s).\n"
                               "You can specify an alternative path with %s" %
                               (args.virtualenv_binary, highlight("--use-virtualenv")))

    def assemble(self, args: configargparse.Namespace) -> None:
        print_info("Initializing virtualenv in %s" % args.build_path)
        venv = [args.virtualenv_binary]
        if args.python_binary:
            venv += ["-p", args.python_binary]
        venv += [args.build_path]
        run_process(*venv)

        pip_binary = create_script_path(args.build_path, "pip")
        run_pip = [pip_binary, "install"]
        if args.pip_opts:
            run_pip += args.pip_opts

        if args.upgrade_pip:
            print_info("Making sure that pip and virtualenv are up to date")
            run_process(*run_pip + ["--upgrade", "pip", "virtualenv"])

        print_info("Installing pip packages")
        if args.packages:
            run_process(*run_pip + args.packages)

        envpy = create_script_path(args.build_path, "python")
        if args.setuppy_install:
            print_info("Installing setup.py packages")
            for path in args.setuppy_install:
                print()
                print("******** %s ********" % highlight(os.path.join(path, "setup.py")))
                os.chdir(path)
                run_spy = [envpy, "setup.py", "install"]
                run_process(*run_spy)

    def print_help(self) -> None:
        print("VirtualEnv Assembler\n"
              "====================\n"
              "\n"
              "%s\n" % (highlight("TODO"),))


assembler_class = VirtualEnvAssembler  # type: Type[VirtualEnvAssembler]
