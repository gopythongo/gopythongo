# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import configargparse
import shlex
import json
import os

from typing import Any, List, Dict, Union, Type

from gopythongo.packers import BasePacker
from gopythongo.utils import template, print_info, highlight, run_process, ErrorMessage, flatten, cmdargs_unquote_split
from gopythongo.utils.buildcontext import the_context, PackerArtifact


class FPMPacker(BasePacker):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @staticmethod
    def _get_fpm_opts_parser(*, i_know_what_im_doing: bool=False) -> configargparse.ArgumentParser:
        """
        Don't use this directly unless you know what you're doing. Use _parse_fpm_opts instead unless you really need
        the argparse.ArgumentParser instance. Due to argparse quirks, you really want to remove whitespace from all
        parsed arguments (else "-n gopythongo" will return args.package_name==" gopythongo").
        """
        if not i_know_what_im_doing:
            raise ValueError("Read the docs for _get_fpm_opts_parser, please")

        parser = configargparse.ArgumentParser()
        parser.add_argument("-n", "--name", dest="package_name", default="")
        parser.add_argument("-p", "--package", dest="package_file", default="")
        return parser

    def _parse_fpm_opts(self, cmdline: List[str]) -> Dict[str, str]:
        inp = vars(self._get_fpm_opts_parser(i_know_what_im_doing=True).parse_known_args(cmdline)[0])
        return {k: v.strip() for k, v in inp.items()}

    @staticmethod
    def _convert_hash_to_dict(ruby_hash: str) -> Dict[str, str]:
        dict_str = ruby_hash.replace(":", '"')     # Remove the ruby object key prefix
        dict_str = dict_str.replace("=>", '" : ')  # swap the k => v notation, and close any unshut quotes
        dict_str = dict_str.replace('""', '"')     # strip back any double quotes we created to sinlges
        return json.loads(dict_str)

    def _parse_fpm_output(self, fpm_output: str) -> Dict[str, str]:
        # find the Ruby hash and crudely convert it into a Python one
        try:
            dic = self._convert_hash_to_dict(fpm_output[fpm_output.index("{"):fpm_output.index("}") + 1])
        except json.JSONDecodeError as e:
            raise ErrorMessage("Can't parse FPM output (%s). Output was: %s" % (str(e), fpm_output)) from e

        return dic

    @property
    def packer_name(self) -> str:
        return "fpm"

    @property
    def provides(self) -> List[str]:
        return ["deb", "rpm"]

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        gr_fpm = parser.add_argument_group("FPM Packer options")
        gr_fpm.add_argument("--use-fpm", dest="fpm", default="/usr/local/bin/fpm",
                            env_var="FPM_EXECUTABLE",
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
        gr_opts.add_argument("--fpm-opts", dest="fpm_extra_opts", default="", env_var="FPM_OPTS",
                             help="Any string specified here will be directly appended to the FPM command-line when it "
                                  "is invoked, allowing you to specify arbitrary extra command-line parameters. Make "
                                  "sure that you use an equals sign, i.e. --fpm-opts='' to avoid 'Unknown parameter' "
                                  "errors! (http://bugs.python.org/issue9334).")

    def validate_args(self, args: configargparse.Namespace) -> None:
        if args.is_inner and not os.path.exists(args.fpm) or not os.access(args.fpm, os.X_OK):
            raise ErrorMessage("fpm not found in path or not executable (%s).\n"
                               "You can specify an alternative executable using %s" %
                               (args.fpm, highlight("--use-fpm")))

        if args.run_fpm:
            for opts in args.run_fpm:
                if opts.startswith("template:"):
                    opts = opts[len("template:"):]
                if not os.path.exists(opts) or not os.access(opts, os.R_OK):
                    raise ErrorMessage("It seems that fpm will not be able to read %s under the user id that "
                                       "GoPythonGo is running under." % opts)

    def _read_fpm_opts_from_file(self, optsfile: str, *, process_templates: bool=True,
                                 ctx: Union[Dict[str, Any], None]) -> List[str]:
        if process_templates and ctx is None:
            raise ValueError("_read_fpm_opts_from_file must be provided with a ctx if process_templates is True")

        with open(optsfile, mode="rt", encoding="utf-8") as f:
            opts = f.readlines()

        if process_templates:
            for ix, line in enumerate(opts):
                opts[ix] = template.strip_comments(line).strip()
                pswt = template.parse_template_prefixes(line)
                if pswt:
                    tplfn = []  # type: List[str]
                    for tpl in pswt.templates:
                        tplfn.append(template.process_to_tempfile(tpl, ctx))
                    opts[ix] = pswt.format_str.format(*tplfn)

        for ix, line in enumerate(opts):
            opts[ix] = line.strip()  # remove whitespace and newlines

        return opts

    def _load_fpm_opts(self, filespec: str, *, process_templates: bool=True,
                       ctx: Union[Dict[str, Any], None]) -> List[str]:
        if process_templates and ctx is None:
            raise ValueError("_load_fpm_opts must be provided with a ctx if process_templates is True")

        pswt = template.parse_template_prefixes(filespec)
        if pswt:
            if len(pswt.templates) > 1:
                raise ErrorMessage("%s can only take a single file argument, there seem to be multiple templates "
                                   "specified." % highlight("--run-fpm"))
            if process_templates:
                thefile = template.process_to_tempfile(pswt.templates[0], ctx if ctx else {})
            else:
                thefile = pswt.templates[0]
        else:
            thefile = filespec

        return self._read_fpm_opts_from_file(thefile, process_templates=process_templates, ctx=ctx)

    def predict_future_artifacts(self, args: configargparse.Namespace) -> Union[List[str], None]:
        ctx = {
            "basedir": args.build_path,
            "buildctx": the_context,
        }

        ret = []  # type: List[str]
        for ix, fpm_opts in enumerate(args.run_fpm):
            processed_args = self._load_fpm_opts(fpm_opts, process_templates=False, ctx=ctx)
            parsed_args = self._parse_fpm_opts(processed_args)
            ret.append(parsed_args["package_name"])

        return ret if len(ret) > 0 else None

    def pack(self, args: configargparse.Namespace) -> None:
        # TODO: don't use deb here, fpm works universally
        fpm_base = [
            args.fpm, "-t", "deb", "-s", "dir",
        ]

        if args.fpm_extra_opts:
            fpm_base += cmdargs_unquote_split(args.fpm_extra_opts)

        ctx = {
            "basedir": args.build_path,
            "buildctx": the_context,
        }

        for ix, fpm_opts in enumerate(args.run_fpm):
            print_info("Running FPM run %s of %s" % (ix + 1, len(args.run_fpm)))

            # hen meet egg. We need to process the fpm_opts template to read the package name to get the actual
            # version string that we generated before and then rerender the fpm_opts template with the real version
            # string
            preparsed_args = self._parse_fpm_opts(
                self._load_fpm_opts(fpm_opts, process_templates=False, ctx=ctx)
            )

            if preparsed_args["package_name"] not in the_context.generated_versions:
                raise ErrorMessage("FPM was instructed to create a package file in the build environment which was not "
                                   "in the list of predicted packages outside of the build environment. This should "
                                   "never happen (unexpected package name: %s, predicted names and versions %s)" %
                                   (preparsed_args["package_name"], str(the_context.generated_versions)))

            ctx["debian_version"] = the_context.generated_versions[preparsed_args["package_name"]]
            del preparsed_args  # make sure we don't accidentally use this below
            processed_args = self._load_fpm_opts(fpm_opts, process_templates=True, ctx=ctx)
            parsed_args = self._parse_fpm_opts(processed_args)

            # now let's go create the package
            if parsed_args["package_file"]:
                if os.path.exists(parsed_args["package_file"]):
                    print_info("%s already exists, will be removed and recreated" %
                               highlight(parsed_args["package_file"]))
                    os.unlink(parsed_args["package_file"])

            run_params = list(fpm_base)  # operate on a copy so we don't change fpm_base
            for argline in processed_args:
                run_params += shlex.split(argline)
            fpm_out = run_process(*run_params)

            out_file = ""
            if parsed_args["package_file"]:
                if not os.path.exists(parsed_args["package_file"]):
                    raise ErrorMessage("File not found: %s expected to exist from parsed FPM opts" %
                                       highlight(parsed_args["package_file"]))
                out_file = parsed_args["package_file"]
            else:
                parsed_output = self._parse_fpm_output(fpm_out.output)
                if "path" in parsed_output:
                    if not os.path.exists(parsed_output["path"]):
                        raise ErrorMessage("File not found: %s expected to exist from parsed FPM output (%s)" %
                                           (highlight(parsed_output["path"]), fpm_out))
                    out_file = parsed_output["path"]
                else:
                    raise ErrorMessage("Running FPM did not result in an output file. Unable to find a %s property in "
                                       "FPM's output or an output filename parameter (-p) in the FPM opts file (%s)" %
                                       (highlight(":path"), highlight(fpm_opts)))

            print_info("FPM: %s created" % highlight(out_file))

            the_context.packer_artifacts.add(PackerArtifact(
                "deb",
                out_file,
                {"package_name": parsed_args["package_name"]},
                self,
                self.packer_name
            ))

    def print_help(self) -> None:
        print("%s\n"
              "==========\n"
              "\n"
              "The FPM packer uses the excellent fpm tool to build Debian packages. It reads\n"
              "a file that contains one fpm command-line parameter per line, commonly located\n"
              "in %s.\n"
              "\n"
              "TODO: Example\n" % (highlight("FPM Packer"), highlight(".gopythongo/fpm_opts")))


packer_class = FPMPacker  # type: Type[FPMPacker]
