# -* encoding: utf-8 *-
import argparse

import os
import sys
import shutil

from gopythongo.packers import BasePacker
from gopythongo.utils import template, print_error, print_info, highlight
from typing import Any, List

from gopythongo.utils.buildcontext import the_context


class FPMPacker(BasePacker):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def packer_name(self) -> str:
        return u"fpm"

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        gr_fpm = parser.add_argument_group("FPM related options (can also be used in OPTS_FILE):")
        gr_fpm.add_argument("--use-fpm", dest="fpm", default="/usr/local/bin/fpm",
                            help="The full path to the fpm executable to use")
        gr_fpm.add_argument("--run-fpm", dest="run_fpm", action="append", metavar="OPTS_FILE",
                            default=[], const=".gopythongo/fpm_opts", nargs="?",
                            help="Execute FPM (can be used multiple times). You must pass a filename to this "
                                 "parameter, which specifies a file containing the command-line parameters for "
                                 "invoking FPM (one per line). FPM will be invoked with the CWD set to the build "
                                 "folder inside the selected builder. You can use template processing here. "
                                 "Default opts file: .gopythongo/fpm_opts")

        gr_deb = parser.add_argument_group("Debian .deb settings")
        gr_deb.add_argument("--package-name", dest="package_name",
                            help="The canonical package name to set using 'fpm -n'")

        gr_opts = parser.add_argument_group("FPM related options (can also be used in OPTS_FILE):")
        gr_opts.add_argument("--fpm-format", dest="fpm_format", choices=["deb"], default="deb",
                             help="Output package format. Only 'deb' is supported for now")
        gr_opts.add_argument("--fpm-opts", dest="fpm_opts", action="append",
                             help="Any string specified here will be directly appended to the FPM command-line when it "
                                  "is invoked, allowing you to specify arbitrary extra command-line parameters. Make "
                                  "sure that you use an equals sign, i.e. --fpm-opts='' to avoid 'Unknown parameter' "
                                  "errors! (http://bugs.python.org/issue9334). You can use 'template:' processing IN "
                                  "THE FPM_OPTS FILE itself and FOR the FPM_OPTS file.")

    def validate_args(self, args: argparse.Namespace) -> None:
        if not os.path.exists(args.fpm) or not os.access(args.fpm, os.X_OK):
            print_error("fpm not found in path or not executable (%s).\n"
                        "You can specify an alternative executable using %s" %
                        (args.fpm, highlight("--use-fpm")))
            sys.exit(1)

        if args.fpm_format == "deb" and not args.package_name:
            print_error("%s requires %s" % (highlight("--fpm_format=deb"), highlight("--package-name")))
            sys.exit(1)

        if args.fpm_opts:
            error_found = False
            for opts in args.fpm_opts:
                if not os.path.exists(opts) or not os.access(opts, os.R_OK):
                    print_error("It seems that fpm will not be able to read %s under the user id that GoPythonGo is "
                                "running under." % opts)
                    error_found = True
            if error_found:
                sys.exit(1)

    def _load_fpm_opts(self, optsfile: str) -> List[str]:
        f = open(optsfile, mode="rt", encoding="utf-8")
        opts = f.readlines()
        f.close()

        for ix in range(0, len(opts)):
            opts[ix] = opts[ix].strip()
        return opts

    def _create_deb(self, outfile: str, path: str, package_name: str, args: argparse.Namespace) -> None:
        fpm_deb = [
            args.fpm, "-t", "deb", "-s", "dir", "-n", package_name,
        ]

        ctx = {
            "basedir": path,
            "buildctx": the_context,
        }

        if args.repo:
            # TODO: compare outfile and _args.repo and copy built package
            # if necessary then update repo index
            pass

    def _build_deb(self, args: argparse.Namespace) -> None:
        print('Creating .deb of %s in %s' % (args.build_path, args.outfile,))
        self._create_deb(args.outfile, args.build_path, args.package_name, args)

    def pack(self, args: argparse.Namespace) -> None:
        self.validate_args(args)
        self._build_deb(args)

        print_info("Cleaning up")
        shutil.rmtree(args.build_path)


packer_class = FPMPacker
