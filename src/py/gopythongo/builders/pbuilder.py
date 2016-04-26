# -* encoding: utf-8 *-

import os
import sys
import shlex

from gopythongo.utils import print_error, print_info, highlight, run_process, flatten, create_script_path
from gopythongo.utils.buildcontext import the_context

builder_name = u"pbuilder"


def add_args(parser):
    gr_pbuilder = parser.add_argument_group("Pbuilder options")
    gr_pbuilder.add_argument("--use-pbuilder", dest="pbuilder_executable", default="/usr/sbin/pbuilder",
                             help="Specify an alternative pbuilder executable.")
    gr_pbuilder.add_argument("--basetgz", dest="basetgz", default=None,
                             help="Cache and reuse the pbuilder base environment. gopythongo will call pbuilder create "
                                  "on this file if it doesn't exist.")
    gr_pbuilder.add_argument("--distribution", dest="pbuilder_distribution", default=None,
                             help="Use this distribution for creating the pbuilder environment using debootstrap.")
    gr_pbuilder.add_argument("--pbuilder-force-recreate", dest="pbuilder_force_recreate", action="store_true",
                             help="Delete the base environment if it exists already.")
    gr_pbuilder.add_argument("--apt-get", dest="build_deps", action="append", default=[],
                             help="Packages to install using apt-get prior to creating the virtualenv (e.g. driver "
                                  "libs for databases so that Python C extensions compile correctly.")
    gr_pbuilder.add_argument("--pbuilder-opts", dest="pbuilder_opts", action="append", default=[],
                             help="Options which will be put into every pbuilder command-line executed by gopythongo.")
    gr_pbuilder.add_argument("--pbuilder-create-opts", dest="pbuilder_create_opts", action="append", default=[],
                             help="Options which will be appended to the pbuilder --create command-line.")
    gr_pbuilder.add_argument("--pbuilder-execute-opts", dest="pbuilder_execute_opts", action="append", default=[],
                             help="Options which will be appended to the pbuilder --execute command-line.")


def validate_args(args):
    if not os.path.exists(args.pbuilder_executable) or not os.access(args.pbuilder_executable, os.X_OK):
        print_error("pbuilder not found in path or not executable (%s).\n"
                    "You can specify an alternative path using %s" % (args.pbuilder_executable,
                                                                      highlight("--use-pbuilder")))
        sys.exit(1)

    if args.basetgz and os.path.exists(args.basetgz) and not os.path.isfile(args.basetgz):
        print_error("pbuilder basetgz %s\nexists but is not a file. Can't continue with this inconsistency." %
                    highlight(args.basetgz))
        sys.exit(1)

    if os.getuid() != 0:
        print_error("pbuilder requires root privileges. Please run GoPythonGo as root when using pbuilder")
        sys.exit(1)


def build(args):
    print_info("Building with %s" % highlight("pbuilder"))

    if args.basetgz and os.path.exists(args.basetgz) and not args.pbuilder_force_recreate:
        return

    if args.basetgz and os.path.exists(args.basetgz) and args.pbuilder_force_recreate:
        os.unlink(args.basetgz)

    create_cmdline = [args.pbuilder_executable, "--create"]
    create_cmdline += shlex.split(" ".join(flatten(args.pbuilder_opts)))
    create_cmdline += shlex.split(" ".join(flatten(args.pbuilder_create_opts)))
    if args.pbuilder_distribution:
        create_cmdline += ["--distribution", args.pbuilder_distribution]

    if args.basetgz:
        create_cmdline += ["--basetgz", args.basetgz]

    if args.build_deps:
        create_cmdline += ["--extrapackages", " ".join(args.build_deps)]

    #run_process(*create_cmdline)

    build_cmdline = [args.pbuilder_executable, "--execute"]

    if args.mounts:
        build_cmdline += ["--bindmounts", " ".join(args.mounts)]

    if args.basetgz:
        build_cmdline += ["--basetgz", args.basetgz]

    build_cmdline += ["--"] + the_context.gopythongo_cmd + ["--inner"] + sys.argv[1:]
    print("***")
    print(str(build_cmdline))
    #run_process(*build_cmdline, "--", create_script_path(args.))
