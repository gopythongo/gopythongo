# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os

from typing import Type

import configargparse

from gopythongo.assemblers import BaseAssembler
from gopythongo.utils import create_script_path, run_process, cmdargs_unquote_split, print_info, highlight, ErrorMessage
from gopythongo.utils.buildcontext import the_context


class CertifyBuildAssembler(BaseAssembler):
    @property
    def assembler_name(self) -> str:
        return "certifybuild"

    @property
    def assembler_type(self) -> str:
        return BaseAssembler.TYPE_PREISOLATION

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        gp_cert = parser.add_argument_group("Certify build options")
        gp_cert.add_argument("--vaultgetcert-config", dest="vaultgetcert_config", default=[], action="append",
                             env_var="CERTIFYBUILD_CONFIG",
                             help="Specify one or more config files for vaultgetcert.")
        gp_cert.add_argument("--vaultgetcert-opts", dest="vaultgetcert_opts", default="",
                             env_var="CERTIFYBUILD_OPTS",
                             help="Specify arguments for the execution of vaultgetcert.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        if args.vaultgetcert_config:
            for cfg in args.vaultgetcert_config:
                if not os.path.exists(cfg) or not os.path.isfile(cfg) or not os.access(cfg, os.R_OK):
                    raise ErrorMessage("%s is not a file or not readable for gopythongo (%s)" %
                                       (highlight(cfg), highlight("--vaultgetcert-config")))

    def assemble(self, args: configargparse.Namespace) -> None:
        cmdargs = [create_script_path(the_context.gopythongo_path, "vaultgetcert")]
        if args.vaultgetcert_config:
            for ix, cfg in enumerate(args.vaultgetcert_config):
                print_info("Certifying build with vaultgetcert %s/%s" % (ix + 1, len(args.vaultgetcert_config)))
                cmd = cmdargs + ["-c", cfg]
                cmd += cmdargs_unquote_split(args.vaultgetcert_opts)
                run_process(*cmd)
        else:
            print_info("Certifying build with vaultgetcert")
            cmd = cmdargs + cmdargs_unquote_split(args.vaultgetcert_opts)
            run_process(*cmd)

    def print_help(self) -> None:
        print("Certify build Assembler\n"
              "=======================\n"
              "\n"
              "This Assembler will run before the build process is isolated by a GoPythonGo\n"
              "Builder and execute gopythongo.vaultgetcert. This allows you to create\n"
              "build-specific X.509 certificates for authentication with services in your\n"
              "deployment environment.\n"
              "\n"
              "It is good practice to configure this so your build server provides\n"
              "configuration files for your individual Vault-backed CAs and passes them into\n"
              "the builds using the CERTIFYBUILD_CONFIG environment variable.\n"
              "\n"
              "Alternatively, you can also jsut standardize your build environments and\n"
              "certification Vault instances to a point where one vaultgetcert configuration\n"
              "file fits your need and you can include it into your SCM.\n")


assembler_class = CertifyBuildAssembler  # type: Type[CertifyBuildAssembler]
