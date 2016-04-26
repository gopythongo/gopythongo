# -* encoding: utf-8 *-

import sys
import os

from gopythongo import utils
from gopythongo.utils import print_error, highlight

assembler_name = "django"


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


def validate_args(args):
    if args.static_outfile or args.collect_static:
        if not (args.static_outfile and args.collect_static):
            print_error("%s and %s must be used together" %
                        (highlight("--static-out"), highlight("--collect-static")))
            sys.exit(1)


def _collect_static():
    global _args
    envpy = utils.create_script_path(_args.build_path, "python")
    print("Collecting static artifacts")
    if os.path.exists(_args.static_root):
        print("    %s exists." % _args.static_root)
        if _args.fresh_static:
            shutil.rmtree(_args.static_root)

    django_admin = utils.create_script_path(_args.build_path, 'django-admin.py')
    run_dja = [envpy, django_admin, "collectstatic"]
    if _args.django_settings_module:
        run_dja.append('--settings=%s' % _args.django_settings_module)
    run_dja.append("--noinput")
    run_dja.append("--traceback")
    utils.run_process(*run_dja)
