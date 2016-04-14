#!/usr/bin/python -u
# -* encoding: utf-8 *-

from gopythongo import utils

import sys
import os


def add_parser(subparsers):
    parser = subparsers.add_parser(name="assemble",
                                   description="",
                                   help="assemble a build inside a container or chroot.")

    gr_django = parser.add_argument_group("Django options")
    gr_django.add_argument("--collect-static", dest="collect_static", action="store_true",
                           help="run 'django-admin.py collectstatic' inside the bundle")
    gr_django.add_argument("--static-out", dest="static_outfile",
                           help="collect static files in STATIC_OUTFILE instead of inside the " +
                                "bundle. Must be used with '--collect-static'.")
    gr_django.add_argument("--static-relative-paths", dest="static_relative",
                           default=False, action="store_true",
                           help="write relative paths to the resulting static content .tar.gz archive")
    gr_django.add_argument("--static-root", dest="static_root", default="static/",
                           help="where to collect static files from (Django's STATIC_ROOT)")
    gr_django.add_argument("--assert-static-root-empty", dest="fresh_static", action="store_true",
                           help="if set, this script will make sure that STATIC_ROOT is empty " +
                                "before running collectstatic by DELETING it (be careful!)")
    gr_django.add_argument("--keep-staticroot", dest="remove_static",
                           default=True, action="store_false",
                           help="will make sure that STATIC_ROOT is NOT removed before bundling the " +
                                "virtualenv. This way the static files may end up in the virtualenv " +
                                "bundle")
    gr_django.add_argument("--django-settings", dest="django_settings_module",
                           help="'--settings' argument to pass to django-admin.py when it is called by " +
                                "this script")

    gr_pip = parser.add_argument_group("PIP options")
    gr_pip.add_argument("--pip-opts", dest="pip_opts", action="append",
                        help="Any string specified here will be directly appended to all pip command-lines when it is "
                             "invoked, allowing you to specify arbitrary extra command-line parameters. Make sure "
                             "that you use an equals sign, i.e. --pip-opts='' to avoid 'Unknown "
                             "parameter' errors! http://bugs.python.org/issue9334")

    gr_setuppy = parser.add_argument_group("Additional source packages")
    gr_setuppy.add_argument("--setuppy-install", dest="setuppy_install", action="append",
                            help="After all pip commands have run, this can run 'python setup.py install' on " +
                                 "additional packages available in any filesystem path. This option can be " +
                                 "used multiple times.")


def validate_args(args):
    pass


def execute(args):
    if args.build_deps:
        print("*** Installing apt-get dependencies")
        utils.run_process("/usr/bin/sudo", "/usr/bin/apt-get", *args.build_deps)

    print("*** Creating bundle %s" % args.outfile)
    print("Initializing virtualenv in %s" % args.build_path)
    utils.run_process(args.virtualenv_binary, args.build_path)
    os.chdir(args.build_path)

    print("")
    print("Installing pip packages")
    pip_binary = utils.create_script_path(args.build_path, "pip")

    run_pip = [pip_binary, "install"]
    if args.pip_opts:
        run_pip += args.pip_opts
    run_pip += args.packages
    utils.run_process(*run_pip)

    envpy = utils.create_script_path(args.build_path, "python")
    if args.setuppy_install:
        print("")
        print("Installing setup.py packages")
        for path in args.setuppy_install:
            if not (os.path.exists(path) and os.path.exists(os.path.join(path, "setup.py"))):
                print("Cannot run setup.py in %s because it does not exist" % path)
                sys.exit(1)
            os.chdir(path)
            run_spy = [envpy, "setup.py", "install"]
            utils.run_process(*run_spy)
