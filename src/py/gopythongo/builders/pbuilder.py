# -* encoding: utf-8 *-
import configargparse
import tempfile
import shlex
import os

from typing import Any, Type

from gopythongo.builders import BaseBuilder, get_dependencies
from gopythongo.utils import print_info, highlight, run_process, print_debug, ErrorMessage
from gopythongo.utils.buildcontext import the_context


class PbuilderBuilder(BaseBuilder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def builder_name(self) -> str:
        return "pbuilder"

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        gr_pbuilder = parser.add_argument_group("Pbuilder Builder options")
        gr_pbuilder.add_argument("--use-pbuilder", dest="pbuilder_executable", default="/usr/sbin/pbuilder",
                                 help="Specify an alternative pbuilder executable")
        gr_pbuilder.add_argument("--basetgz", dest="basetgz", default="/var/cache/pbuilder/base.tgz", env_var="BASETGZ",
                                 help="Cache and reuse the pbuilder base environment. gopythongo will call pbuilder "
                                      "create on this file if it doesn't exist")
        gr_pbuilder.add_argument("--distribution", dest="pbuilder_distribution", default=None, env_var="DISTRIBUTION",
                                 help="Use this distribution for creating the pbuilder environment using debootstrap.")
        gr_pbuilder.add_argument("--pbuilder-force-recreate", dest="pbuilder_force_recreate", action="store_true",
                                 help="Delete the base environment if it exists already")
        gr_pbuilder.add_argument("--pbuilder-reprovision", dest="pbuilder_reprovision", action="store_true",
                                 default=False,
                                 help="Run all --run-after-create commands regardless of whether the pbuilder base "
                                      "environment already exists.")
        gr_pbuilder.add_argument("--pbuilder-opts", dest="pbuilder_opts", default="", env_var="PBUILDER_OPTS",
                                 help="Options which will be put into every pbuilder command-line executed by "
                                      "GoPythonGo")
        gr_pbuilder.add_argument("--pbuilder-create-opts", dest="pbuilder_create_opts", default="",
                                 env_var="PBUILDER_CREATE_OPTS",
                                 help="Options which will be appended to the pbuilder --create command-line")
        gr_pbuilder.add_argument("--pbuilder-execute-opts", dest="pbuilder_execute_opts", default="",
                                 env_var="PBUILDER_EXECUTE_OPTS",
                                 help="Options which will be appended to the pbuilder --execute command-line")
        gr_pbuilder.add_argument("--apt-get", dest="build_deps", action="append", default=[],
                                 help="Packages to install using apt-get prior to creating the virtualenv (e.g. driver "
                                      "libs for databases so that Python C extensions compile correctly")
        gr_pbuilder.add_argument("--no-install-defaults", dest="install_defaults", action="store_false",
                                 default=True,
                                 help="By default GoPythonGo will always install python, python-virtualenv, "
                                      "python-pip, python[3]-dev, virtualenv and possibly eatmydata. If you set this "
                                      "flag you will have to install python using --apt-get, or GoPythonGo will not be "
                                      "able to run inside the container, but this gives you more control about what "
                                      "Python version runs.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        if args.is_inner:
            pass
        else:
            # validate things we only need to validate in the outer layer
            if not os.path.exists(args.pbuilder_executable) or not os.access(args.pbuilder_executable, os.X_OK):
                raise ErrorMessage("pbuilder not found in path or not executable (%s).\n"
                                   "You can specify an alternative path using %s" %
                                   (args.pbuilder_executable, highlight("--use-pbuilder")))

            if args.basetgz and os.path.exists(args.basetgz) and not os.path.isfile(args.basetgz):
                raise ErrorMessage("pbuilder basetgz %s exists but is not a file. Can't continue with this "
                                   "inconsistency." % highlight(args.basetgz))

            if not args.pbuilder_distribution:
                raise ErrorMessage("pbuilder distribution unfortunately defaults to %s, so you must explicitly set it "
                                   "using the parameter %s" %
                                   (highlight("sid (unstable)"), highlight("--distribution")))
            elif ("debian/%s" % args.pbuilder_distribution) not in _builder_args.get_dependencies() \
                    and args.install_defaults:
                raise ErrorMessage("GoPythonGo does not have stored package dependencies for distribution %s. You can "
                                   "set %s to ignore this error." %
                                   (highlight(args.pbuilder_distribution), highlight("--no-install-defaults")))

            if os.getuid() != 0:
                raise ErrorMessage("pbuilder requires root privileges. Please run GoPythonGo as root when using "
                                   "pbuilder")

    def build(self, args: configargparse.Namespace) -> None:
        print_info("Building with %s" % highlight("pbuilder"))

        do_create = True
        if args.basetgz and os.path.exists(args.basetgz) and not args.pbuilder_force_recreate:
            do_create = False

        if args.basetgz and os.path.exists(args.basetgz) and args.pbuilder_force_recreate:
            os.unlink(args.basetgz)

        if do_create:
            create_cmdline = [args.pbuilder_executable, "--create"]
            create_cmdline += shlex.split(args.pbuilder_opts)
            create_cmdline += shlex.split(args.pbuilder_create_opts)
            if args.pbuilder_distribution:
                create_cmdline += ["--distribution", args.pbuilder_distribution]

            if args.basetgz:
                create_cmdline += ["--basetgz", args.basetgz]

            if args.install_defaults:
                args.build_deps += get_dependencies()["debian/%s" % args.pbuilder_distribution]
                if args.eatmydata:
                    args.build_deps += ["eatmydata"]

            if args.build_deps:
                create_cmdline += ["--extrapackages", " ".join(args.build_deps)]

            run_process(*create_cmdline)

        build_args = []  # type: List[str]
        build_args += shlex.split(args.pbuilder_opts)
        build_args += shlex.split(args.pbuilder_execute_opts)

        for mount in args.mounts + list(the_context.mounts):
            build_args += ["--bindmounts", mount]

        if args.basetgz:
            build_args += ["--basetgz", args.basetgz]

        if do_create or args.pbuilder_reprovision:
            for ix, runspec in enumerate(args.run_after_create):
                print_info("Running post-creation commands for build environment %s of %s" %
                           (highlight(str(ix + 1)), highlight(str(len(args.run_after_create)))))
                if os.path.isfile(os.path.abspath(runspec)):
                    runspec = os.path.abspath(runspec)
                post_create_cmdline = [args.pbuilder_executable, "--execute"] + build_args + \
                                      ["--save-after-exec", "--", runspec]
                run_process(*post_create_cmdline)

        if args.builder_debug_login:
            build_cmdline = [args.pbuilder_executable, "--login"] + build_args
            debug_cmdline = build_cmdline + ["--"] + the_context.get_gopythongo_inner_commandline()
            debug_cmdline = [x if x != "--login" else "--execute" for x in debug_cmdline]
            print_debug("Without --builder-debug-login, GoPythonGo would have run: %s" % " ".join(debug_cmdline))
        else:
            # pbuilder COPIES the first argument after "--" to the chroot and executes it, so we can't reference
            # the GoPythonGo python interpreter directly. Instead we need to create a intermediary script file
            from gopythongo.main import tempfiles
            build_cmdline = [args.pbuilder_executable, "--execute"] + build_args + ["--"]
            scriptfd, scriptfn = tempfile.mkstemp()
            tempfiles.append(scriptfn)
            with open(scriptfd, "wt", encoding="utf-8") as f:
                print("#!/bin/sh", file=f)
                print(" ".join(the_context.get_gopythongo_inner_commandline()), file=f)
            print_debug("Running the following command inside the build environment: %s" %
                        " ".join(the_context.get_gopythongo_inner_commandline()))
            build_cmdline += [scriptfn]

        run_process(*build_cmdline, interactive=args.builder_debug_login)

    def print_help(self) -> None:
        print("Pbuilder Builder\n"
              "================\n"
              "\n"
              "Builds virtualenvs in a chroot using Debian's pbuilder. This has the drawback,\n"
              "that GoPythonGo needs to run as root to utilize pbuilder correctly, as it needs\n"
              "chroot privileges (you might be able to do something using fakeroot and setcap\n"
              "cap_sys_chroot, but that's untested).\n")


builder_class = PbuilderBuilder  # type: Type[PbuilderBuilder]
