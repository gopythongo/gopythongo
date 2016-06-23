# -* encoding: utf-8 *-
import argparse
import shutil
import sys
import os

from typing import Any

from gopythongo import utils
from gopythongo.assemblers import BaseAssembler
from gopythongo.utils import print_error, highlight


class DjangoAssembler(BaseAssembler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def assembler_name(self) -> str:
        return u"django"

    def add_parser(self, parser: argparse.ArgumentParser) -> None:
        gr_django = parser.add_argument_group("Django Assembler options")
        gr_django.add_argument("--collect-static", dest="collect_static", action="store_true",
                               help="run 'django-admin.py collectstatic' inside the bundle")
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

    def validate_args(self, args: argparse.Namespace) -> None:
        if args.static_outfile or args.collect_static:
            if not (args.static_outfile and args.collect_static):
                print_error("%s and %s must be used together" %
                            (highlight("--static-out"), highlight("--collect-static")))
                sys.exit(1)

    def _collect_static(self, args: argparse.Namespace) -> None:
        envpy = utils.create_script_path(args.build_path, "python")
        print("Collecting static artifacts")
        if os.path.exists(args.static_root):
            print("    %s exists." % args.static_root)
            if args.fresh_static:
                shutil.rmtree(args.static_root)

        django_admin = utils.create_script_path(args.build_path, 'django-admin.py')
        run_dja = [envpy, django_admin, "collectstatic"]
        if args.django_settings_module:
            run_dja.append('--settings=%s' % args.django_settings_module)
        run_dja.append("--noinput")
        run_dja.append("--traceback")
        utils.run_process(*run_dja)


assembler_class = DjangoAssembler
