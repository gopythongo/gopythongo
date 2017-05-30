# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import configargparse
from typing import Type, Any
from gopythongo.builders import BaseBuilder, get_dependencies
from gopythongo.utils import print_info, highlight, run_process, print_debug
from gopythongo.utils.buildcontext import the_context


class NoIsolationBuilder(BaseBuilder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def builder_name(self) -> str:
        return "noisolation"

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        pass

    def validate_args(self, args: configargparse.Namespace) -> None:
        pass

    def build(self, args: configargparse.Namespace) -> None:
        print_info("Building with %s" % highlight("no isolation"))

        if args.install_pkgs:
            create_cmdline = ["apt-get", "--no-install-recommends", "-q", "-y" , "-o",
                              "DPkg::Options::=--force-confold", "-o", "DPkg::Options::=--force-confdef", "install"]
            create_cmdline += args.install_pkgs

            run_process(*create_cmdline)

        for ix, runspec in enumerate(args.run_after_create):
            print_info("Running preparation commands for build environment %s of %s" %
                       (highlight(str(ix + 1)), highlight(str(len(args.run_after_create)))))
            if os.path.isfile(os.path.abspath(runspec)):
                runspec = os.path.abspath(runspec)
                run_process(runspec)

        print_debug("Running the build command: %s" % " ".join(the_context.get_gopythongo_inner_commandline()))
        run_process(*the_context.get_gopythongo_inner_commandline())

    def print_help(self) -> None:
        print("No isolation Builder\n"
              "====================\n"
              "\n"
              "Run a build without any isolation.\n"
              "\n"
              "GoPythonGo can use Pbuilder or Docker to isolate builds. However, many build\n"
              "servers already isolate builds. Since it's senseless  run containers in\n"
              "containers, this builder allows GoPythonGo to do its job without isolation.\n"
              "\n"
              "As the name says, this Builder basically just runs all --after-create arguments\n"
              "and then executes the 'inner' build, i.e. the part of GoPythonGo that would run\n"
              "in a container with other Builders. This will definitely modify the build host's\n"
              "filesystem.\n")


builder_class = NoIsolationBuilder  # type: Type[NoIsolationBuilder]
