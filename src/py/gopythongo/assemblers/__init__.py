# -* encoding: utf-8 *-

import os
import sys

from gopythongo.utils import run_process, create_script_path, print_info, print_error, highlight

assemblers = {
    ""
}


def add_args(parser):
    gr_pip = parser.add_argument_group("PIP options")
    gr_pip.add_argument("--pip-opts", dest="pip_opts", action="append", default=[],
                        help="Any string specified here will be directly appended to all pip command-lines when it is "
                             "invoked, allowing you to specify arbitrary extra command-line parameters. Make sure "
                             "that you use an equals sign, i.e. --pip-opts='' to avoid 'Unknown "
                             "parameter' errors! http://bugs.python.org/issue9334")

    gr_setuppy = parser.add_argument_group("Additional source packages")
    gr_setuppy.add_argument("--setuppy-install", dest="setuppy_install", action="append", default=[],
                            help="After all pip commands have run, this can run 'python setup.py install' on " +
                                 "additional packages available in any filesystem path. This option can be " +
                                 "used multiple times.")

    pos_args = parser.add_argument_group("Python ecosystem arguments (positional)")
    pos_args.add_argument("build_path",
                          help="set the location where the virtual environment will be built, this " +
                               "is IMPORTANT as it is also the location where the virtualenv must " +
                               "ALWAYS reside (i.e. the install directory. Virtualenvs are NOT relocatable" +
                               "by default! All path parameters are relative to this path.")
    pos_args.add_argument("packages", metavar="package<=>version", nargs="+",
                          help="a list of package/version specifiers. Remember to quote your " +
                               "strings as in \"Django>=1.6,<1.7\"")


def validate_args(args):
    if not os.path.isabs(args.build_path):
        print_error("build_path must be an absolute path. %s is not absolute." % highlight(args.build_path))
        sys.exit(1)

    for path in args.setuppy_install:
        if not (os.path.exists(path) and os.path.exists(os.path.join(path, "setup.py"))):
            print_error("Cannot run setup.py in %s, because it does not exist" % highlight(path))
            sys.exit(1)


def assemble(args):
    print_info("Initializing virtualenv in %s" % args.build_path)
    run_process(args.virtualenv_binary, args.build_path)
    os.chdir(args.build_path)

    print_info("Installing pip packages")
    pip_binary = create_script_path(args.build_path, "pip")

    run_pip = [pip_binary, "install"]
    if args.pip_opts:
        run_pip += args.pip_opts
    run_pip += args.packages
    run_process(*run_pip)

    envpy = create_script_path(args.build_path, "python")
    if args.setuppy_install:
        print_info("Installing setup.py packages")
        for path in args.setuppy_install:
            print()
            print("******** %s ********" % highlight(os.path.join(path, "setup.py")))
            os.chdir(path)
            run_spy = [envpy, "setup.py", "install"]
            run_process(*run_spy)
