# -* encoding: utf-8 *-
import argparse
import json

import os

from typing import Any, List, Dict

from gopythongo.packers import BasePacker
from gopythongo.utils import template, print_info, highlight, run_process, ErrorMessage
from gopythongo.utils.buildcontext import the_context, PackerArtifact


class FPMPacker(BasePacker):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @staticmethod
    def _get_fpm_opts_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument("-n", "--name", dest="package_name", default="")
        parser.add_argument("-p", "--package", dest="package_file", default="")
        return parser

    @staticmethod
    def _convert_hash_to_dict(ruby_hash: str) -> Dict[str, str]:
        dict_str = ruby_hash.replace(":",'"')    # Remove the ruby object key prefix
        dict_str = dict_str.replace("=>",'" : ') # swap the k => v notation, and close any unshut quotes
        dict_str = dict_str.replace('""','"')    # strip back any double quotes we created to sinlges
        return json.loads(dict_str)

    def _parse_fpm_output(self, fpm_output: str) -> Dict[str, str]:
        # find the Ruby dict
        try:
            dic = self._convert_hash_to_dict(fpm_output[fpm_output.index("{"):fpm_output.index("}") + 1])
        except json.JSONDecodeError as e:
            raise ErrorMessage("Can't parse FPM output (%s). Output was: %s" % (str(e), fpm_output)) from e

        return dic

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
                                 "folder inside the selected builder. Templating is supported. You can use 'template:' "
                                 "prefixes INSIDE THE OPTS_FILE ITSELF and also process OPTS_FILE as a template. "
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
            raise ErrorMessage("fpm not found in path or not executable (%s).\n"
                               "You can specify an alternative executable using %s" %
                               (args.fpm, highlight("--use-fpm")))

        if args.fpm_opts:
            for opts in args.fpm_opts:
                if not os.path.exists(opts) or not os.access(opts, os.R_OK):
                    raise ErrorMessage("It seems that fpm will not be able to read %s under the user id that "
                                       "GoPythonGo is running under." % opts)

    def _read_fpm_opts_from_file(self, optsfile: str, ctx: Dict[str, Any]) -> List[str]:
        with open(optsfile, mode="rt", encoding="utf-8") as f:
            opts = f.readlines()

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
                raise ErrorMessage("%s can only take a single file argument, there seem to be multiple templates "
                                   "specified." % highlight("--fpm-opts"))
            thefile = template.process_to_tempfile(pswt.templates[0], ctx)
        else:
            thefile = filespec

        return self._read_fpm_opts_from_file(thefile, ctx)

    def _run_fpm(self, args: argparse.Namespace) -> None:
        # TODO: don't use deb here, fpm works universally
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
            processed_args = self._load_fpm_opts(args.run_fpm[ix], ctx)
            parsed_args = self._get_fpm_opts_parser().parse_known_args(processed_args)

            if not parsed_args.package_name:
                raise ErrorMessage("FPM opts file MUST contain a package name (-n|--name) parameter (%s)" %
                                   args.run_fpm[ix])

            run_params = fpm_base + processed_args
            fpm_out = run_process(*run_params)

            out_file = ""
            if parsed_args.package_file:
                if not os.path.exists(args.package_file):
                    raise ErrorMessage("File not found: %s expected to exist from parsed FPM opts" %
                                       highlight(args.package_file))
                out_file = parsed_args.package_file
            else:
                parsed_output = self._parse_fpm_output(fpm_out)
                if "path" in parsed_output:
                    if not os.path.exists(parsed_output["path"]):
                        raise ErrorMessage("File not found: %s expected to exist from parsed FPM output (%s)" %
                                           (highlight(parsed_output["path"]), fpm_out))
                    out_file = parsed_output["path"]
                else:
                    raise ErrorMessage("Running FPM did not result in an output file. Unable to find a %s property in "
                                       "FPM's output or an output filename parameter (-p) in the FPM opts file (%s)" %
                                       (highlight(":path"), highlight(args.run_fpm[ix])))

            the_context.packer_artifacts.add(PackerArtifact(
                "deb",
                out_file,
                {"package_name": parsed_args.package_name},
                self,
                self.packer_name
            ))

    def pack(self, args: argparse.Namespace) -> None:
        self._run_fpm(args)


packer_class = FPMPacker
