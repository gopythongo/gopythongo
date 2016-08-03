# -* encoding: utf-8 *-
import configargparse
import os

from docker.client import Client as DockerClient
from docker.tls import TLSConfig
from gopythongo.utils import highlight, ErrorMessage
from requests.exceptions import RequestException

_docker_shared_args_added = False  # type: bool


def add_shared_args(parser: configargparse.ArgumentParser) -> None:
    global _docker_shared_args_added

    if not _docker_shared_args_added:
        gr_docker_shared = parser.add_argument_group("Docker common parameters (Builder and Store)")
        gr_docker_shared.add_argument("--docker-api", dest="docker_api", default="unix://var/run/docker.sock",
                                      help="The Docker API endpoint as a http/unix URL. (Default: "
                                           "unix://var/run/docker.sock)")
        gr_docker_shared.add_argument("--docker-tls-client-cert", dest="docker_tls_client_cert", default=None,
                                      help="Path to a SSL client certificate in PEM format to use when connecting to "
                                           "the Docker API.")
        gr_docker_shared.add_argument("--docker-tls-verify", dest="docker_tls_verify", default=False,
                                      help="Set this to a CA certificate PEM file to verify that the Docker server's "
                                           "TLS certificate was signed by this CA.")
        gr_docker_shared.add_argument("--docker-ssl-version", dest="docker_ssl_version", default=5,
                                      help="Set to 3 (TLSv1), 4 (TLSv1.1) or 5 (TLSv1.2) to force the connection to "
                                           "use a particular protocol version. (Default: 5).")
        gr_docker_shared.add_argument("--docker-tls-noverify-hostname", dest="docker_dont_verify_hostname",
                                      default=False, action="store_true",
                                      help="Set this if the Docker API client should skip verifying the Docker API's "
                                           "hostname.")

    _docker_shared_args_added = True


def get_docker_client(args) -> DockerClient:
    return DockerClient(
        args.docker_api,
        tls=TLSConfig(
            client_cert=args.docker_tls_client_cert,
            ca_cert=args.docker_tls_verify,
            verify=args.docker_tls_verify is not False,
            ssl_version=args.docker_ssl_version,
            assert_hostname=not args.docker_dont_verify_hostname,
        ),
    )


def validate_shared_args(args: configargparse.Namespace) -> None:
    if args.docker_tls_verify:
        if not os.path.isfile(args.docker_tls_verify) or not os.access(args.docker_tls_verify, os.R_OK):
            raise ErrorMessage("File not found: %s (or not readable)" % highlight(args.docker_tls_verify))

    if args.docker_tls_client_cert:
        if not os.path.isfile(args.docker_tls_client_cert) or not os.access(args.docker_tls_client_cert, os.R_OK):
            raise ErrorMessage("File not found: %s (or not readable)" % highlight(args.docker_tls_client_cert))

    try:
        x = int(args.docker_ssl_version)
        if x < 1 or x > 5:
            raise ErrorMessage("Unknown value %s for SSL Protocol version. Valid are values 1-5." %
                               args.docker_ssl_version)
    except ValueError:
        raise ErrorMessage("Parameter to --docker-ssl-version must be an integer between 1 and 5")

    dcl = get_docker_client(args)
    try:
        info = dcl.info()
    except RequestException as e:
        raise ErrorMessage("GoPythonGo can't talk to the Docker API at %s (Error was: %s)" %
                           (highlight(args.docker_api), str(e))) from e
