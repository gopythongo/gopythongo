# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import re
import uuid

import configargparse

from typing import Any, Type

import sys
from gopythongo import utils
from gopythongo.shared import docker_args as _docker_args
from gopythongo.utils import print_info, highlight, ErrorMessage, template, run_process, print_debug, targz, print_error, \
    ProcessOutput, print_warning
from gopythongo.builders import BaseBuilder, get_dependencies
from gopythongo.utils.buildcontext import the_context
from requests.exceptions import RequestException


class DockerBuilder(BaseBuilder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def builder_name(self) -> str:
        return "docker"

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        _docker_args.add_shared_args(parser)

        gp_docker = parser.add_argument_group("Docker Builder options")
        # FIXME: reimplement this using docker-py? docker-py supports streaming so we can output progress
        gp_docker.add_argument("--use-docker", dest="docker_executable", default="/usr/bin/docker",
                               help="Specify an alternative Docker client executable.")
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
        gp_docker.add_argument("--docker-buildarg", dest="docker_buildargs", default=[], action="append",
                               help="Allows you to set Docker build args in the form of 'KEY=VALUE' which will be "
                                    "passed to the Docker daemon and into your Dockerfile as ARGs.")
        gp_docker.add_argument("--dockerfile-var", dest="dockerfile_vars", default=[], action="append",
                               help="Allows you to set Dockerfile Jinja template context variables in the form of "
                                    "'key=value' which will be passed into your Dockerfile template before it is "
                                    "rendered to be sent to the Docker daemon.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        _docker_args.validate_shared_args(args)

        if not os.path.exists(args.docker_executable) or not os.access(args.docker_executable, os.X_OK):
            raise ErrorMessage("docker not found in path or not executable (%s).\n"
                               "You can specify an alternative path using %s" %
                               (args.docker_executable, highlight("--use-docker")))

        if not args.docker_buildfile:
            raise ErrorMessage("Using the docker builder requires you to specify a Dockerfile template via "
                               "--docker-buildfile.")

        if not os.path.exists(args.docker_buildfile) or not os.access(args.docker_buildfile, os.R_OK):
            raise ErrorMessage("It seems that GoPythonGo can't find or isn't allowed to read %s" %
                               highlight(args.docker_buildfile))

        for arg in args.docker_buildargs:
            if "=" not in arg:
                raise ErrorMessage("A Docker build arg must be in the form 'key=value'. Consult the %s "
                                   "documentation for more information. '%s' does not contain a '='." %
                                   (highlight("docker build"), arg))

        for var in args.dockerfile_vars:
            if "=" not in var:
                raise ErrorMessage("A Dockerfile Jinja template context variable must be in the form 'key=value'. "
                                   "'%s' does not contain a '='" % var)

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
        ctx.update({key: value for key, value in [x.split("=", 1) for x in args.dockerfile_vars]})
        dockerfile = template.process_to_tempfile(args.docker_buildfile, ctx)

        # ship all config files in a .tar.gz as context via Docker STDIN
        # then run GoPythonGo in the resulting container with all folders mounted

        from gopythongo.main import config_paths
        memtgz = targz.create_targzip(filename=None,
                                      paths=[(x, x) for x in list(config_paths)] + [(dockerfile, "/Dockerfile",)],
                                      verbose=utils.enable_debug_output)

        if args.docker_debug_save_context:
            with open(args.docker_debug_save_context, "wb") as f:
                print_info("Saving Docker context to %s" % highlight(args.docker_debug_save_context))
                f.write(memtgz.getvalue())

        dcl = _docker_args.get_docker_client(args)

        try:
            build_output = dcl.build(
                fileobj=memtgz.getbuffer(),
                custom_context=True,
                encoding="gzip",
                forcerm=not args.docker_leave_images,
                decode=True,
                buildargs={
                    key: value for key, value in [x.split("=", 1) for x in args.docker_buildargs]
                },
            )
        except RequestException as e:
            raise ErrorMessage("GoPythonGo failed to execute the Docker build API call: %s" % str(e)) from e

        prev_progress = False
        full_output = []
        # do a build with fancy string formatting
        for line in build_output:
            if "progress" in line:
                if not prev_progress:
                    if "id" in line:
                        print_info("Downloading %s" % line["id"])
                    prev_progress = True
                print(line["progress"].strip(), end="\r")
            else:
                if prev_progress:
                    print()
                    prev_progress = False

                if "stream" in line:
                    print_debug(line["stream"].strip())
                    full_output.append(line["stream"].strip())
                elif "error" in line:
                    raise ErrorMessage("Docker build failed with error message: %s" % line["error"])

        m = re.search("Successfully built ([0-9a-zA-Z]+)", "\n".join(full_output))
        if m:
            build_container_id = m.group(1)
        else:
            raise ErrorMessage("Unable to find the container ID of the build container, so GoPythonGo can't "
                               "execute the build. Check the docker output for reasons.")

        temp_container_name = "gopythongo-%s" % str(uuid.uuid4())

        volumes = []
        for mount in args.mounts + list(the_context.mounts):
            # docker makes problems if you mount subfolders of the same path, so we filter those
            parent_mounted = False
            for chkmount in args.mounts + list(the_context.mounts):
                if mount.startswith(chkmount) and len(mount) > len(chkmount):
                    parent_mounted = True
            if not parent_mounted:
                if os.path.isdir(mount) and mount[-1] != os.path.sep:
                    mount = "%s%s" % (mount, os.path.sep)  # append a trailing slash for folders
                # in docker-py, you add a "mountpoint definition" for create_container then specify the bindmount
                # on .start(binds=)
                volumes.append(mount)

        import gopythongo.main  # import for later use of break_handlers
        import dockerpty  # dockerpty imports fcntl which will fail on Windows, so we can't import it at the top

        if args.builder_debug_login:
            print_info("Without --builder-debug-login, inside this container GoPythonGo would have run: %s" %
                       " ".join(the_context.get_gopythongo_inner_commandline()))
            try:
                build_container = dcl.create_container(
                    image=build_container_id,
                    command="/bin/bash",
                    volumes=volumes,
                    name=temp_container_name,
                    working_dir=os.getcwd(),
                    environment={
                        "PYTHONUNBUFFERED": "0"
                    },
                    tty=True,
                    stdin_open=True,
                )

                dockerpty.start(dcl, build_container, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
            except RequestException as e:
                raise ErrorMessage("Failed to create Docker container from image %s: %s" %
                                   (highlight(build_container_id), highlight(str(e)))) from e
        else:
            try:
                # while the container is running, make sure we kill it when the user hits CTRL+C
                build_container = dcl.create_container(
                    image=build_container_id,
                    command=the_context.get_gopythongo_inner_commandline(),
                    volumes=volumes,
                    name=temp_container_name,
                    working_dir=os.getcwd(),
                    environment={
                        "PYTHONUNBUFFERED": "0"
                    },
                )

                def killlambda() -> None:
                    print_info("Stopping and removing build container %s" % build_container["Id"])
                    dcl.kill(build_container["Id"])
                    dcl.remove_container(build_container["Id"])

                gopythongo.main.break_handlers["docker-kill"] = killlambda

                dcl.start(
                    build_container["Id"],
                    binds={
                        k: k for k in volumes
                    },
                )

                run_output = dcl.logs(build_container["Id"], stream=True)
            except RequestException as e:
                raise ErrorMessage("Failed to create Docker container from image %s: %s" %
                                   (highlight(build_container_id), highlight(str(e)))) from e

            full_output = []
            for line in run_output:
                if isinstance(line, bytes):
                    line = line.decode("utf-8")
                line = line.strip()
                full_output.append(line)
                print("| %s" % line)

            # after the build has finished remove the break_handler
            del gopythongo.main.break_handlers["docker-kill"]

        if not args.docker_leave_containers:
            print_info("Removing build container %s" % temp_container_name)
            try:
                dcl.remove_container(temp_container_name)
            except RequestException as e:
                raise ErrorMessage("Failed to remove the temporary build container %s: %s" %
                                   (highlight(temp_container_name), highlight(str(e)))) from e

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
              "    2. GoPythonGo executes inside that build container and builds a virtualenv\n"
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
              "\n"
              "The build container is then run by GoPythonGo." %
              (",\n".join(["                           %s" % x for x in get_dependencies()["debian/jessie"]])))


class DockerBuilderWin32(DockerBuilder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        print_warning("Docker builder is unavailable on Win32 for lack of fcntl")
        super().__init__(*args, **kwargs)

    def validate_args(self, args: configargparse.Namespace) -> None:
        return

    def build(self, args: configargparse.Namespace) -> None:
        print_error("Docker builder is unavailable on Win32 for lack of fcntl")
        sys.exit(1)


if sys.platform.startswith("win32"):
    builder_class = DockerBuilderWin32  # type: Type[DockerBuilder]
else:
    builder_class = DockerBuilder  # type: Type[DockerBuilder]
