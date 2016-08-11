# -* encoding: utf-8 *-
import os

import configargparse
from gopythongo.builders import BaseBuilder
from gopythongo.utils import print_info, highlight, run_process, print_debug
from gopythongo.utils.buildcontext import the_context


class NoIsolationBuilder(BaseBuilder):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(args, kwargs)

    @property
    def builder_name(self) -> str:
        return "noisolation"

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        pass

    def validate_args(self, args: configargparse.Namespace) -> None:
        pass

    def build(self, args: configargparse.Namespace) -> None:
        print_info("Building with %s" % highlight("no isolation"))

        for ix, runspec in enumerate(args.run_after_create):
            print_info("Running preparation commands for build environment %s of %s" %
                       (highlight(str(ix + 1)), highlight(str(len(args.run_after_create)))))
            if os.path.isfile(os.path.abspath(runspec)):
                runspec = os.path.abspath(runspec)
                run_process(runspec)

        print_debug("Running the build command: %s" % " ".join(the_context.get_gopythongo_inner_commandline()))
        run_process(the_context.get_gopythongo_inner_commandline())

    def print_help(self) -> None:
        print("No isolation Builder\n"
              "====================\n"
              "\n"
              "As the name says, this Builder basically just runs all --after-create arguments\n"
              "and then executes the 'inner' build, i.e. the part of GoPythonGo that would run\n"
              "in a container with other Builders. This will definitely modify the build host's\n"
              "filesystem. You should only really use this for build servers which already\n"
              "isolate your builds (like TravisCI) and often don't give you the privileges to\n"
              "run your own isolation layers anyway.\n")

builder_class = NoIsolationBuilder
