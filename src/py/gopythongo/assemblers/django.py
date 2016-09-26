# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
import shutil
import os

from typing import Any, Type

import configargparse

from gopythongo import utils
from gopythongo.assemblers import BaseAssembler
from gopythongo.utils import highlight, ErrorMessage, get_umasked_mode


class DjangoAssembler(BaseAssembler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def assembler_name(self) -> str:
        return u"django"

    @property
    def assembler_type(self) -> str:
        return BaseAssembler.TYPE_ISOLATED

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        gr_django = parser.add_argument_group("Django Assembler options")
        gr_django.add_argument("--collect-static", dest="collect_static", action="store_true", default=False,
                               help="If set, run 'django-admin.py collectstatic' inside the bundle")
        gr_django.add_argument("--static-relative-paths", dest="static_relative",
                               default=False, action="store_true",
                               help="Write relative paths to the resulting static content .tar.gz archive (UNUSED)")
        gr_django.add_argument("--static-root", dest="static_root", default="static/",
                               help="Where to collect static files from (Django's STATIC_ROOT)")
        gr_django.add_argument("--assert-static-root-empty", dest="fresh_static", action="store_true", default=False,
                               help="If set, this script will make sure that STATIC_ROOT is empty " +
                                    "before running collectstatic by DELETING it (be careful!)")
        gr_django.add_argument("--django-settings", dest="django_settings_module", default=None,
                               help="'--settings' argument to pass to django-admin.py when it is called by " +
                                    "this script. If --django-generate-secret-key is set, SECRET_KEY will be set "
                                    "in the environment.")
        gr_django.add_argument("--django-gen-secret-key", dest="django_secret_key_file", default=None,
                               env_var="DJANGO_GEN_SECRET_KEY",
                               help="If set, GoPythonGo will write SECRET_KEY='(random)' to the given filename. The "
                                    "resulting file can be read from envdir or systemd (EnvironmentFile). This is "
                                    "useful for shipping environment configuration for projects adhering to 12factor "
                                    "(and/or using the django12factor library).")

    def validate_args(self, args: configargparse.Namespace) -> None:
        if args.django_secret_key_file:
            if os.path.exists(os.path.dirname(args.django_secret_key_file)):
                if not os.access(os.path.dirname(args.django_secret_key_file), os.W_OK):
                    raise ErrorMessage("GoPythonGo can't write to %s" % os.path.dirname(args.django_secret_key_file))

                if os.path.exists(args.django_secret_key_file) and not os.access(args.django_secret_key_file, os.W_OK):
                    raise ErrorMessage("GoPythonGo can't write to %s" % args.django_secret_key_file)

    def assemble(self, args: configargparse.Namespace) -> None:
        if args.django_secret_key_file:
            utils.print_info("Creating SECRET_KEY configuration for Django in %s" %
                             utils.highlight(args.django_secret_key_file))
            if not os.path.exists(os.path.dirname(args.django_secret_key_file)):
                utils.umasked_makedirs(os.path.dirname(args.django_secret_key_file), 0o755)

            secret = base64.b64encode(os.urandom(48)).decode("utf-8")
            if args.django_settings_module and 'SECRET_KEY' not in os.environ:
                os.environ['SECRET_KEY'] = secret

            with open(args.django_secret_key_file, "wt", encoding="utf-8") as sf:
                os.chmod(args.django_secret_key_file, get_umasked_mode(0o600))
                sf.write("SECRET_KEY=%s\n" % secret)

        if args.collect_static:
            envpy = utils.create_script_path(args.build_path, "python")
            utils.print_info("Collecting static artifacts")
            if os.path.exists(args.static_root):
                utils.print_debug("    %s exists." % args.static_root)
                if args.fresh_static:
                    utils.print_info("removing stale static artifacts in %s" % args.static_root)
                    shutil.rmtree(args.static_root)

            django_admin = utils.create_script_path(args.build_path, 'django-admin.py')
            run_dja = [envpy, django_admin, "collectstatic"]
            if args.django_settings_module:
                run_dja.append('--settings=%s' % args.django_settings_module)
            run_dja.append("--noinput")
            run_dja.append("--traceback")
            utils.run_process(*run_dja)

            if not os.path.exists(args.static_root):
                raise ErrorMessage("%s should now exist, but it doesn't" % args.static_root)


assembler_class = DjangoAssembler  # type: Type[DjangoAssembler]
