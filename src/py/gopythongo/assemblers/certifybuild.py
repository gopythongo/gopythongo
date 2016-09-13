# -* encoding: utf-8 *-
import configargparse
from gopythongo.assemblers import BaseAssembler


class CertifyBuildAssembler(BaseAssembler):
    @property
    def assembler_name(self) -> str:
        return "certifybuild"

    @property
    def assembler_type(self) -> str:
        return BaseAssembler.TYPE_PREISOLATION

    def assemble(self, args: configargparse.Namespace) -> None:
        pass

    def print_help(self) -> None:
        print("Certify build Assembler\n"
              "=======================\n"
              "\n"
              "This Assembler will run before the build process is isolated by a GoPythonGo\n"
              "Builder and execute gopythongo.vaultgetcert. This allows you to create\n"
              "build-specific X.509 certificates for authentication with services in your\n"
              "deployment environment.\n")


assembler_class = CertifyBuildAssembler
