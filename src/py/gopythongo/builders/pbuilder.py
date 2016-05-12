# -* encoding: utf-8 *-

import os
import sys
import shlex

from gopythongo.builders import BaseBuilder
from gopythongo.utils import print_error, print_info, highlight, run_process, flatten, create_script_path, print_debug
from gopythongo.utils.buildcontext import the_context


class PbuilderBuilder(BaseBuilder):
    def __init__(self, *args, **kwargs):
        super(PbuilderBuilder, self).__init__(*args, **kwargs)

    @property
    def builder_name(self):
        return u"pbuilder"

    def add_args(self, parser):
        gr_pbuilder = parser.add_argument_group("Pbuilder options")
        gr_pbuilder.add_argument("--use-pbuilder", dest="pbuilder_executable", default="/usr/sbin/pbuilder",
                                 help="Specify an alternative pbuilder executable")
        gr_pbuilder.add_argument("--basetgz", dest="basetgz", default="/var/cache/pbuilder/base.tgz",
                                 help="Cache and reuse the pbuilder base environment. gopythongo will call pbuilder "
                                      "create on this file if it doesn't exist")
        gr_pbuilder.add_argument("--distribution", dest="pbuilder_distribution", default=None,
                                 help="Use this distribution for creating the pbuilder environment using debootstrap.")
        gr_pbuilder.add_argument("--pbuilder-force-recreate", dest="pbuilder_force_recreate", action="store_true",
                                 help="Delete the base environment if it exists already")
        gr_pbuilder.add_argument("--no-install-defaults", dest="pbuilder_install_defaults", action="store_false",
                                 default=True,
                                 help="By default GoPythonGo will always install python, python-virtualenv, "
                                      "python-pip, python-dev and possibly eatmydata. If you set this flag you will "
                                      "have to install python using --apt-get, or GoPythonGo will not be able to run "
                                      "inside the container, but this gives you more control about what Python version "
                                      "runs.")
        gr_pbuilder.add_argument("--apt-get", dest="build_deps", action="append", default=[],
                                 help="Packages to install using apt-get prior to creating the virtualenv (e.g. driver "
                                      "libs for databases so that Python C extensions compile correctly")
        gr_pbuilder.add_argument("--pbuilder-opts", dest="pbuilder_opts", action="append", default=[],
                                 help="Options which will be put into every pbuilder command-line executed by "
                                      "GoPythonGo")
        gr_pbuilder.add_argument("--pbuilder-create-opts", dest="pbuilder_create_opts", action="append", default=[],
                                 help="Options which will be appended to the pbuilder --create command-line")
        gr_pbuilder.add_argument("--pbuilder-execute-opts", dest="pbuilder_execute_opts", action="append", default=[],
                                 help="Options which will be appended to the pbuilder --execute command-line")
        gr_pbuilder.add_argument("--pbuilder-debug-login", dest="pbuilder_debug_login", action="store_true",
                                 default=False,
                                 help="Instead of executing the '--inner' build, run pbuilder with '--login' to spawn "
                                      "a debug shell inside the chroot")

    def validate_args(self, args):
        if args.is_inner:
            return

        if not os.path.exists(args.pbuilder_executable) or not os.access(args.pbuilder_executable, os.X_OK):
            print_error("pbuilder not found in path or not executable (%s).\n"
                        "You can specify an alternative path using %s" % (args.pbuilder_executable,
                                                                          highlight("--use-pbuilder")))
            sys.exit(1)

        if args.basetgz and os.path.exists(args.basetgz) and not os.path.isfile(args.basetgz):
            print_error("pbuilder basetgz %s\nexists but is not a file. Can't continue with this inconsistency." %
                        highlight(args.basetgz))
            sys.exit(1)

        if not args.pbuilder_distribution:
            print_error("pbuilder distribution unfortunately defaults to %s, so you must explicitly set it using "
                        "the parameter %s" %
                        (highlight("sid (unstable)"), highlight("--distribution")))
            sys.exit(1)

        if os.getuid() != 0:
            print_error("pbuilder requires root privileges. Please run GoPythonGo as root when using pbuilder")
            sys.exit(1)

    def build(self, args):
        print_info("Building with %s" % highlight("pbuilder"))

        do_create = True
        if args.basetgz and os.path.exists(args.basetgz) and not args.pbuilder_force_recreate:
            do_create = False

        if args.basetgz and os.path.exists(args.basetgz) and args.pbuilder_force_recreate:
            os.unlink(args.basetgz)

        if do_create:
            create_cmdline = [args.pbuilder_executable, "--create"]
            create_cmdline += shlex.split(" ".join(flatten(args.pbuilder_opts)))
            create_cmdline += shlex.split(" ".join(flatten(args.pbuilder_create_opts)))
            if args.pbuilder_distribution:
                create_cmdline += ["--distribution", args.pbuilder_distribution]

            if args.basetgz:
                create_cmdline += ["--basetgz", args.basetgz]

            if args.pbuilder_install_defaults:
                args.build_deps += ["python", "python-pip", "python-dev", "python-virtualenv"]
                if args.eatmydata:
                    args.build_deps += ["eatmydata"]

            if args.build_deps:
                create_cmdline += ["--extrapackages", " ".join(args.build_deps)]

            run_process(*create_cmdline)

        if args.pbuilder_debug_login:
            build_cmdline = [args.pbuilder_executable, "--login"]
        else:
            build_cmdline = [args.pbuilder_executable, "--execute"]

        mounts = ""
        if args.mounts:
            mounts += " ".join(args.mounts)

        if the_context.mounts:
            if mounts:
                mounts += " "
            mounts += " ".join(the_context.mounts)

        if mounts:
            build_cmdline += ["--bindmounts", mounts]

        if args.basetgz:
            build_cmdline += ["--basetgz", args.basetgz]

        if args.pbuilder_debug_login:
            debug_cmdline = build_cmdline + ["--"] + the_context.gopythongo_cmd + ["--inner"] + sys.argv[1:]
            debug_cmdline = [x if x != "--login" else "--execute" for x in debug_cmdline]
            print_debug("Without --login, GoPythonGo would run: %s" % " ".join(debug_cmdline))
        else:
            build_cmdline += ["--"] + the_context.gopythongo_cmd + ["--inner"] + sys.argv[1:]

        run_process(*build_cmdline)


builder_class = PbuilderBuilder
