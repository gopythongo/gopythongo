# -* encoding: utf-8 *-
import argparse
import os

from typing import Dict, Any

from gopythongo.utils import run_process, create_script_path, print_info, highlight, plugins, \
    CommandLinePlugin, ErrorMessage

assemblers = {}  # type: Dict[str, 'BaseAssembler']


def init_subsystem() -> None:
    global assemblers

    from gopythongo.assemblers import django
    assemblers = {
        u"django": django.assembler_class(),
    }

    plugins.load_plugins("gopythongo.assemblers", assemblers, "assembler_class", BaseAssembler, "assembler_name")


class BaseAssembler(CommandLinePlugin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def assembler_name(self) -> str:
        """
        **@property**
        """
        raise NotImplementedError("Each subclass of BaseAssembler MUST implement assembler_name")

    def assemble(self, args: argparse.Namespace) -> None:
        pass


def add_args(parser: argparse.ArgumentParser) -> None:
    global assemblers

    gr_pip = parser.add_argument_group("PIP Assembler options")
    gr_pip.add_argument("--pip-opts", dest="pip_opts", action="append", default=[],
                        help="Any string specified here will be directly appended to all pip command-lines when it is "
                             "invoked, allowing you to specify arbitrary extra command-line parameters, like "
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
                           help="Set an alternative virtualenv binary to use inside the builder container")
    gr_python.add_argument("--python-binary", dest="python_binary", default="python3",
                           help="Force virtualenv to use a certain Python version (Default: 'python3'). This will be "
                                "passed to virtualenv's -p parameter. You must change this if you want to build and "
                                "ship Python 2.x virtual environments.")

    pos_args = parser.add_argument_group("Python ecosystem arguments (positional)")
    pos_args.add_argument("build_path",
                          help="set the location where the virtual environment will be built, this " +
                               "is IMPORTANT as it is also the location where the virtualenv must " +
                               "ALWAYS reside (i.e. the install directory. Virtualenvs are NOT relocatable" +
                               "by default! All path parameters are relative to this path")
    pos_args.add_argument("packages", metavar="package<=>version", nargs="*",
                          help="a list of package/version specifiers. Remember to quote your " +
                               "strings as in \"Django>=1.9,<1.10\"")

    for assembler in assemblers.values():
        assembler.add_args(parser)


def validate_args(args: argparse.Namespace) -> None:
    if not os.path.isabs(args.build_path):
        raise ErrorMessage("build_path must be an absolute path. %s is not absolute." % highlight(args.build_path))

    for path in args.setuppy_install:
        if not (os.path.exists(path) and os.path.exists(os.path.join(path, "setup.py"))):
            raise ErrorMessage("Cannot run setup.py in %s, because it does not exist" % highlight(path))

    for assembler in args.assemblers:
        if assembler in assemblers.keys():
            assemblers[assembler].validate_args(args)


def assemble(args: argparse.Namespace) -> None:
    pip_binary = create_script_path(args.build_path, "pip")
    run_pip = [pip_binary, "install"]
    if args.pip_opts:
        run_pip += args.pip_opts

    if args.upgrade_pip:
        print_info("Making sure that pip and virtualenv are up to date")
        run_process(*run_pip + ["--upgrade", "pip", "virtualenv"])

    print_info("Initializing virtualenv in %s" % args.build_path)
    venv = [args.virtualenv_binary]
    if args.python_binary:
        venv += ["-p", args.python_binary]
    venv += [args.build_path]
    run_process(*venv)

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
