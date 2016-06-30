# -* encoding: utf-8 *-
import argparse

import os
import sys
import shutil

from gopythongo.packers import BasePacker
from gopythongo.utils import template, print_error, print_info, highlight, run_process
from typing import Any, List, Dict

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
                                 "folder inside the selected builder. You can use 'template:' processing IN "
                                 "THE FPM_OPTS FILE itself and FOR the FPM_OPTS file. "
                                 "Default opts file: .gopythongo/fpm_opts")

        gr_opts = parser.add_argument_group("FPM related options (can also be used in OPTS_FILE):")
        gr_opts.add_argument("--fpm-format", dest="fpm_format", choices=["deb"], default="deb",
                             help="Output package format. Only 'deb' is supported for now")
        gr_opts.add_argument("--fpm-opts", dest="fpm_opts", action="append", default=[],
                             help="Any string specified here will be directly appended to the FPM command-line when it "
                                  "is invoked, allowing you to specify arbitrary extra command-line parameters. Make "
                                  "sure that you use an equals sign, i.e. --fpm-opts='' to avoid 'Unknown parameter' "
                                  "errors! (http://bugs.python.org/issue9334).")

    def validate_args(self, args: argparse.Namespace) -> None:
        if not os.path.exists(args.fpm) or not os.access(args.fpm, os.X_OK):
            print_error("fpm not found in path or not executable (%s).\n"
                        "You can specify an alternative executable using %s" %
                        (args.fpm, highlight("--use-fpm")))
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

    def _read_fpm_opts_from_file(self, optsfile: str, ctx: Dict[str, Any]) -> List[str]:
        f = open(optsfile, mode="rt", encoding="utf-8")
        opts = f.readlines()
        f.close()

        for ix in range(0, len(opts)):
            opts[ix] = opts[ix].strip()
            pswt = template.parse_template_prefixes(opts[ix])
            if pswt:
                tplfn = []  # type: List[str]
                for tpl in pswt.templates:
                    tplfn.append(template.process_to_tempfile(tpl, ctx))
                opts[ix] = pswt.format_str.format(*tplfn)

        return opts

    def _load_fpm_opts(self, filespec: str, ctx: Dict[str, Any]) -> List[str]:
        pswt = template.parse_template_prefixes(filespec)
        if pswt:
            if len(pswt.templates) > 1:
                print_error("%s can only take a single file argument, there seem to be multiple templates "
                            "specified." % highlight("--fpm-opts"))
                sys.exit(1)
            thefile = template.process_to_tempfile(pswt.templates[0], ctx)
        else:
            thefile = filespec

        return self._read_fpm_opts_from_file(thefile, ctx)

    def _run_fpm(self, args: argparse.Namespace) -> None:
        # TODO: don't use deb here
        # TODO: we have to specify package names somehow for aptly, but still allow multiple fpm runs
        fpm_base = [
            args.fpm, "-t", "deb", "-s", "dir",
        ]

        fpm_base += args.fpm_opts

        ctx = {
            "basedir": args.build_path,
            "buildctx": the_context,
        }

        for ix in range(args.run_fpm):
            print_info("Running FPM run %s of %s" % (ix, len(args.run_fpm)))
            run_params = fpm_base + self._load_fpm_opts(args.run_fpm[ix], ctx)
            run_process(*run_params)

    def pack(self, args: argparse.Namespace) -> None:
        self._run_fpm(args)


packer_class = FPMPacker
