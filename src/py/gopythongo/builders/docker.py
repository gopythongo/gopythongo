# -* encoding: utf-8 *-
import os
import re
import uuid

import configargparse

from typing import Any, Type

from gopythongo import utils
from gopythongo.shared import docker_args as _docker_args
from gopythongo.utils import print_info, highlight, ErrorMessage, template, run_process, print_debug, targz, print_error, \
    ProcessOutput
from gopythongo.builders import BaseBuilder, get_dependencies
from gopythongo.utils.buildcontext import the_context


class DockerBuilder(BaseBuilder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def builder_name(self) -> str:
        return "docker"

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        _docker_args.add_shared_args(parser)

        gp_docker = parser.add_argument_group("Docker Builder options")
        gp_docker.add_argument("--docker-buildfile", dest="docker_buildfile", default=None,
                               help="Specify a Dockerfile to build the the build environment. The build commands will "
                                    "then be executed inside the resulting container. The file is always processed as "
                                    "a Jinja template and must contain certain variable placeholders. Read "
                                    "--help-builder=docker for more information.")
        gp_docker.add_argument("--docker-leave-containers", dest="docker_leave_containers", action="store_true",
                               default=False, env_var="DOCKER_LEAVE_CONTAINERS",
                               help="After creating a build environment and a runtime container, if this option is "
                                    "used, GoPythonGo will not use 'docker rm' to clean up the resulting containers.")
        gp_docker.add_argument("--docker-leave-images", dest="docker_leave_images", action="store_true",
                               default=False, env_var="DOCKER_LEAVE_IMAGES",
                               help="After creating a build environment and a runtime container, if this option is "
                                    "used, GoPythonGo will not use '--force-rm' to clean up the intermediate build "
                                    "images.")
        gp_docker.add_argument("--docker-debug-savecontext", dest="docker_debug_save_context", default=None,
                               help="Set this to a filename to save the .tar.gz that GoPythonGo assembles as a "
                                    "Docker context to build the build environment container using 'docker build'.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        _docker_args.validate_shared_args(args)

        if not args.docker_buildfile:
            raise ErrorMessage("Using the docker builder requires you to pass --docker-buildfile and specify a "
                               "Dockerfile template.")

        if not os.path.exists(args.docker_buildfile) or not os.access(args.docker_buildfile, os.R_OK):
            raise ErrorMessage("It seems that GoPythonGo can't find or isn't allowed to read %s" %
                               highlight(args.docker_buildfile))

    def _clean_containers(self, docker_return: ProcessOutput) -> None:
        container_ids = re.findall("---> Running in ([0-9a-zA-Z]+)", docker_return.output)
        for c in reversed(container_ids):
            print_error("Remove container %s" % c)
            run_process("docker", "rm", c, allow_nonzero_exitcode=True)

    def build(self, args: configargparse.Namespace) -> None:
        print_info("Building with %s" % highlight("docker"))
        ctx = {
            "run_after_create": args.run_after_create,
            "dependencies": get_dependencies()
        }
        dockerfile = template.process_to_tempfile(args.docker_buildfile, ctx)

        # ship all config files in a .tar.gz as context via Docker STDIN
        # then run GoPythonGo in the resulting container with all folders mounted

        from gopythongo.main import config_paths
        memtgz = targz.create_targzip(filename=None,
                                      paths=list(config_paths) + [(dockerfile, "/Dockerfile",)],
                                      verbose=utils.enable_debug_output)

        if args.docker_debug_save_context:
            with open(args.docker_debug_save_context, "wb") as f:
                print_info("Saving Docker context to %s" % highlight(args.docker_debug_save_context))
                f.write(memtgz.getvalue())

        build_cmdline = ["docker", "build"]
        if not args.docker_leave_images:
            build_cmdline += ["--force-rm"]
        build_cmdline += ["-"]
        print_debug("Running Docker build from %s" % highlight(dockerfile))
        res = run_process(*build_cmdline, send_to_stdin=memtgz.getvalue(), allow_nonzero_exitcode=True)

        if res.exitcode != 0:
            if not args.docker_leave_containers:
                self._clean_containers(res)
            raise ErrorMessage("'%s' exited with a non-zero exitcode (%s). Output was:\n%s" %
                               (" ".join(build_cmdline), res.exitcode, res.output))
        else:
            m = re.search("Successfully built ([0-9a-zA-Z]+)", res.output)
            if m:
                build_container_id = m.group(1)
            else:
                raise ErrorMessage("Unable to find the container ID of the build container, so GoPythonGo can't "
                                   "execute the build. Check the docker output for reasons.")

        # give the container a unique name so we can remove it later
        temp_container_name = "gopythongo-%s" % str(uuid.uuid4())
        gpg_cmdline = ["docker", "run", "-a", "STDOUT", "-a", "STDERR", "-e", "PYTHONUNBUFFERED=0", "--name",
                       temp_container_name, "-w", "/gopythongo/output"]

        for mount in args.mounts + list(the_context.mounts):
            # docker makes problems if you mount subfolders of the same path, so we filter those
            parent_mounted = False
            for chkmount in args.mounts + list(the_context.mounts):
                if mount.startswith(chkmount) and len(mount) > len(chkmount):
                    parent_mounted = True
            if not parent_mounted:
                if os.path.isdir(mount) and mount[-1] != os.path.sep:
                    mount = "%s%s" % (mount, os.path.sep)
                gpg_cmdline += ["-v", "%s:%s" % (mount, mount)]

        gpg_cmdline += ["-v", "%s:/gopythongo/output" % os.getcwd()]

        if args.builder_debug_login:
            debug_cmdline = gpg_cmdline + [build_container_id]
            debug_cmdline += the_context.get_gopythongo_inner_commandline(cwd="/gopythongo/output")
            gpg_cmdline += ["-i", "-t", "-a", "STDIN", "-a", "STDOUT", "-a", "STDERR", build_container_id, "/bin/bash"]
            print_debug("Without --builder-debug-login, GoPythonGo would have run: %s" % " ".join(debug_cmdline))
        else:
            gpg_cmdline = gpg_cmdline + [build_container_id]
            gpg_cmdline += the_context.get_gopythongo_inner_commandline(cwd="/gopythongo/output")

        print_info("Starting build container %s" % temp_container_name)
        res = run_process(*gpg_cmdline, interactive=args.builder_debug_login, allow_nonzero_exitcode=True)

        if not args.docker_leave_containers:
            print_info("Removing build container %s" % temp_container_name)
            run_process("docker", "rm", temp_container_name)

        if res.exitcode != 0:
            raise ErrorMessage("Inner GoPythonGo build in the Docker container failed. Please read the build jobs "
                               "output for more information.")

    def print_help(self) -> None:
        print("Docker Builder\n"
              "==============\n"
              "\n"
              "Builds virtualenvs in a Docker container. This requires GoPythonGo to either\n"
              "run as root or the user running GoPythonGo to be a member of the docker group.\n"
              "To run Docker GoPythonGo relies on templated build Dockerfile which you can\n"
              "customize to represent your later production runtime setup. Please note that\n"
              "the build container used by the Docker Builder is not a container which you\n"
              "should ship later, since it will likely contain compilers, header files and\n"
              "other helpers. Instead create a minimal production Docker container from the\n"
              "build container's output later, using the GoPythonGo Docker Store, for example.\n"
              "\n"
              "The Docker build process runs in 3 steps:\n"
              "    1. A build container is created using 'docker build' if it doesn't exist\n"
              "       yet, containing sources, header files and compilers as needed.\n"
              "    2. GoPythonGo executes inside that build container and builds a virtualenv"
              "       using 'docker run'. This can't be done in step 1 because docker doesn't\n"
              "       allow the mounting of host folders during build time.\n"
              "    3. The build artifacts are extracted from the build container and the\n"
              "       container is removed.\n"
              "\n"
              "The build Dockerfile template must contain the following variables to build\n"
              "the container:\n"
              "\n"
              "    {{run_after_create}} - is a list of commands to run via the RUN directive\n"
              "                           of the Dockerfile. Include it in your Dockerfile\n"
              "                           template like this:\n"
              "                               {%% for cmd in run_after_create %%}\n"
              "                               RUN {{cmd}}\n"
              "                               {%% endfor %%}\n"
              "\n"
              "You can optionally use the following variables in the template:\n"
              "\n"
              "    {{dependencies}} - resolves to a dictionary of distribution names to lists\n"
              "                       of package names that are common dependencies required\n"
              "                       to build virtualenvs for each platform. Distribution\n"
              "                       names have the form 'debian/jessie'. This is just for\n"
              "                       convenience.\n"
              "                       For example: {{dependencies['debian/jessie']}} will\n"
              "                       resolve to:\n"
              "%s\n"
              "The build container is then run by GoPythonGo" %
              (",\n".join(["                           %s" % x for x in get_dependencies()["debian/jessie"]])))


builder_class = DockerBuilder  # type: Type[DockerBuilder]
