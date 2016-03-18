#!/usr/bin/python -u
# -* encoding: utf-8 *-

from configargparse import ArgParser as ArgumentParser
from gopythongo import utils

import sys
import os


_args = None


def get_parser():
    parser = ArgumentParser(description="",
                            fromfile_prefix_chars="@",
                            default_config_files=["./.gopythongo"],
                            add_config_file_help=False,
                            prog="gopythongo.main assemble")

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
    gr_pip.add_argument("--pip-opt", dest="pip_opts", action="append",
                        help="option string to pass to pip (can be used multiple times). Make sure " +
                             "that you use an equals sign, i.e. --pip-opt='' to avoid 'Unknown " +
                             "parameter' errors! http://bugs.python.org/issue9334")

    gr_setuppy = parser.add_argument_group("Additional source packages")
    gr_setuppy.add_argument("--setuppy-install", dest="setuppy_install", action="append",
                            help="after all pip commands have run, this can run 'python setup.py install' on " +
                                 "additional packages available in any filesystem path. This option can be " +
                                 "used multiple times.")

    return parser


def validate_args():
    pass


def parse_args():
    pass


def main():
    if _args.build_deps:
        print('*** Installing apt-get dependencies')
        utils.run_process('/usr/bin/sudo', '/usr/bin/apt-get', *_args.build_deps)

    print('*** Creating bundle %s' % _args.outfile)
    print('Initializing virtualenv in %s' % _args.build_path)
    utils.run_process(_args.virtualenv_binary, _args.build_path)
    os.chdir(_args.build_path)

    print('')
    print('Installing pip packages')
    pip_binary = utils.create_script_path(_args.build_path, 'pip')

    run_pip = [pip_binary, "install"]
    if _args.pip_opts:
        run_pip += _args.pip_opts
    run_pip += _args.packages
    utils.run_process(*run_pip)

    envpy = utils.create_script_path(_args.build_path, 'python')
    if _args.setuppy_install:
        print('')
        print('Installing setup.py packages')
        for path in _args.setuppy_install:
            if not (os.path.exists(path) and os.path.exists(os.path.join(path, 'setup.py'))):
                print('Cannot run setup.py in %s because it does not exist' % path)
                sys.exit(1)
            os.chdir(path)
            run_spy = [envpy, 'setup.py', 'install']
            utils.run_process(*run_spy)
