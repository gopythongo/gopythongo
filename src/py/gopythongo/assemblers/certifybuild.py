# -* encoding: utf-8 *-
from typing import Type

import configargparse

from gopythongo.assemblers import BaseAssembler
from gopythongo.utils import create_script_path, run_process, cmdargs_unquote_split
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
        gp_cert.add_argument("--vaultgetcert-opts", dest="vaultgetcert_opts", default="",
                             help="Specify arguments for the execution of vaultgetcert.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        pass

    def assemble(self, args: configargparse.Namespace) -> None:
        cmdargs = [create_script_path(the_context.gopythongo_path, "vaultgetcert")]
        cmdargs += cmdargs_unquote_split(args.vaultgetcert_opts)
        run_process(*cmdargs)

    def print_help(self) -> None:
        print("Certify build Assembler\n"
              "=======================\n"
              "\n"
              "This Assembler will run before the build process is isolated by a GoPythonGo\n"
              "Builder and execute gopythongo.vaultgetcert. This allows you to create\n"
              "build-specific X.509 certificates for authentication with services in your\n"
              "deployment environment.\n")


assembler_class = CertifyBuildAssembler  # type: Type[CertifyBuildAssembler]
