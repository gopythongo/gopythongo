# -* encoding: utf-8 *-
import os
import sys
import hvac
import subprocess
import configargparse

from typing import List, Sequence, Iterable, Union, Any

from requests.exceptions import RequestException


class HelpAction(configargparse.Action):
    def __init__(self,
                 option_strings: Sequence[str],
                 dest: str,
                 default: Any=None,
                 choices: Iterable[Any]=None,
                 help: str="Show help for GoPythonGo version parsers.") -> None:
        super().__init__(option_strings=option_strings, dest=dest, default=default,
                         nargs="?", choices=choices, help=help)

    def __call__(self, parser: configargparse.ArgumentParser, namespace: configargparse.Namespace,
                 values: Union[str, Sequence[Any], None], option_string: str=None) -> None:
        print("Secret Management\n"
              "=================\n"
              "\n"
              "This is a little helper tool that contacts a Vault server to issue a SSL client\n"
              "certificate and save its X.509 certificate and private key to local files. If\n"
              "you use this on your build server to create client certificates for each\n"
              "ontinuous Integration (CD) build, you can create client credentials for\n"
              "accessing Vault instances or databases or other services on your environments\n"
              "right on your buildserver. In my opinion this is the best place for the\n"
              "credentials to live, since they can be dynamic and don't need to live in either\n"
              "your configuration management software (Puppet/Chef/Ansible/Salt) or in your\n"
              "application. Both places which are often shared far and wide throughout your\n"
              "organization.\n"
              "\n"
              "Instead giving each build its own certificate and each deployment environment\n"
              "(development/stage/production) it's own (intermediate) CA does not detract from\n"
              "security (you have to trust your CD infrastructure implicitly, if it's\n"
              "compromised, the attacker can deploy malicious code), but makes it much easier\n"
              "to, for example, revoke access credentials in bulk using CRLs.\n"
              "\n"
              "Finally, you can use the created certificates to access a separate Vault\n"
              "instance inside your deployment environments and create local service\n"
              "credentials there (like short-lived database access credentials). Thereby\n"
              "using Vault's audit backends to create a secure offsite audit trail of activity.\n"
              "\n"
              "Here is a cheatsheet for setting up a PKI endpoint in Vault:\n"
              "\n"
              "# Mount one PKI backend per environment that gets its own builds on this server\n"
              "# and allow builds to remain valid for 1 year (tune to your specifications\n"
              "vault mount -path=pki-dev -default-lease-ttl=8760h -max-lease-ttl=8760h pki\n"
              "\n"
              "# generate an intermediate CA with a 2048 bit key (default)\n"
              "vault write pki-dev/intermediate/generate/internal \\\n"
              "    common_name=\"Automated Build CA X1\"\n"
              "\n"
              "# Sign the intermediate CA using your private CA\n"
              "# then write the certificate back to the Vault store\n"
              "vault write pki-dev/intermediate/set-signed certificate=-\n"
              "\n"
              "# Now this CA certificate should be installed on the relevant servers, e.g. in\n"
              "# Postgres ssl_ca_cert. You can also use the root certificate with a trustchain\n"
              "# in the client certificate.\n"
              "vault write pki-dev/roles/build ttl=8760h allow_localhost=false \\\n"
              "    allow_ip_sans=false server_flag=false client_flag=true \\\n"
              "    allow_any_name=true key_type=rsa\n"
              "\n"
              "# Request a build certificate for a build\n"
              "# We \"hack\" the git hash into a domain name SAN because Vault currently\n"
              "# doesn't support freetext SANs. This should run in your build scripts.\n"
              "vault write pki-dev/issue/build common_name=\"vaultadmin\" \\\n"
              "    alt_names=\"024572834273498734.git\" exclude_cn_from_sans=true\n")
        parser.exit(0)


def get_parser() -> configargparse.ArgumentParser:
    parser = configargparse.ArgumentParser(
        description="This is a little helper tool that contacts a Vault server to issue a SSL client "
                    "certificate and save its X.509 certificate and private key to local files. Use "
                    "--help-verbose to learn more.",
        prog="gopythongo.vaultwrapper",
        args_for_setting_config_path=["-c"],
        config_arg_help_message="Use this path instead of the default (.gopythongo/vaultwrapper)",
        default_config_files=[".gopythongo/vaultgetcert",]
    )

    parser.add_argument("--address", dest="vault_address", default="https://vault.local:8200",
                        env_var="VAULT_URL", help="Vault URL")
    parser.add_argument("--cert-key", dest="cert_key", default=None, required=True,
                        env_var="VAULT_CERT_KEY",
                        help="The key path to issue a certificate from Vault.")
    parser.add_argument("--subject-alt-names", dest="subject_alt_names", default=None,
                        help="alt_names to pass to Vault for the issued certificate.")
    parser.add_argument("--common-name", dest="common_name", default=None, required=True,
                        help="The CN to pass to Vault for the issued certificate.")
    parser.add_argument("--include-cn-in-sans", dest="include_cn_in_sans", default=False, action="store_true",
                        help="Set this if you want the value of --common-name to also show up in the issued "
                             "certificate's SANs")
    parser.add_argument("--certfile", dest="certfile", required=True,
                        help="Path of the file where the generated certificate will be stored.")
    parser.add_argument("--keyfile", dest="keyfile", required=True,
                        help="Path of the file where the generated private key will be stored. Permissions for this "
                             "file will be set to 600.")
    parser.add_argument("--overwrite", dest="overwrite", default=False, action="store_true",
                        help="When set, this program will overwrite existing certificates and keys on disk.")
    parser.add_argument("--help-verbose", action=HelpAction,
                        help="Show additional information about how to set up Vault for using vaultgetcert.")

    gp_https = parser.add_argument_group("HTTPS options")
    gp_https.add_argument("--client-cert", dest="client_cert", default=None, env_var="VAULT_CLIENTCERT",
                          help="Use a HTTPS client certificate to connect.")
    gp_https.add_argument("--client-key", dest="client_key", default=None, env_var="VAULT_CLIENTKEY",
                          help="Set the HTTPS client certificate private key.")
    gp_https.add_argument("--pin-cacert", dest="pin_cacert", default="/etc/ssl/certs/ca-certificates.crt",
                          env_var="VAULT_CACERT",
                          help="Set the CA certificate for Vault (i.e. the server certificate MUST be signed by a CA "
                               "in this file). The file should contain a list of CA certificates. The default is the "
                               "location of the Debian Linux CA bundle (Default: '/etc/ssl/certs/ca-certificates.crt')")
    gp_https.add_argument("--tls-skip-verify", dest="verify", default=True, action="store_false",
                          help="Skip SSL verification (only use this during debugging or development!)")

    gp_auth = parser.add_argument_group("Vault authentication options")
    gp_auth.add_argument("--token", dest="vault_token", env_var="VAULT_TOKEN", default=None,
                         help="A Vault access token with a valid lease. This is one way of authenticating the wrapper "
                              "to Vault. This is mutually exclusive with --app-id/--user-id.")
    gp_auth.add_argument("--app-id", dest="vault_appid", env_var="VAULT_APPID", default=None,
                         help="Set the app-id for Vault app-id authentication.")
    gp_auth.add_argument("--user-id", dest="vault_userid", env_var="VAULT_USERID", default=None,
                         help="Set the user-id for Vault app-id authentication.")


def validate_args(args: configargparse.Namespace) -> None:
    if args.vault_token:
        pass
    elif args.vault_appid and args.vault_userid:
        pass
    elif args.client_cert and args.client_key:
        pass
    else:
        print("* ERR VAULT CERT UTIL *: You must specify an authentication method, so you must pass either "
              "--token or --app-id and --user-id or --client-cert and --client-key or set the VAULT_TOKEN, "
              "VAULT_APPID and VAULT_USERID environment variables respectively. If you run GoPythonGo under "
              "sudo (e.g. for pbuilder), make sure your build server environment variables also exist in the "
              "root shell, or build containers, or whatever else you're using.")
        if args.vault_appid:
            print("* INF VAULT CERT UTIL *: appid is set")
        if args.vault_userid:
            print("* INF VAULT CERT UTIL *: userid is set")
        if args.client_cert:
            print("* INF VAULT CERT UTIL *: client_cert is set")
        if args.client_key:
            print("* INF VAULT CERT UTIL *: client_key is set")
        sys.exit(1)

    if args.wrap_program and (not os.path.exists(args.wrap_program) or not os.access(args.wrap_program, os.X_OK)):
        print("* ERR VAULT CERT UTIL *: Wrapped executable %s doesn't exist or is not executable." % args.wrap_program)
        sys.exit(1)

    if args.client_cert and (not os.path.exists(args.client_cert) or not os.access(args.client_cert, os.R_OK)):
        print("* ERR VAULT CERT UTIL *: %s File not found or no read privileges" % args.client_cert)
        sys.exit(1)

    if args.client_key and (not os.path.exists(args.client_key) or not os.access(args.client_key, os.R_OK)):
        print("* ERR VAULT CERT UTIL *: %s File not found or no read privileges" % args.client_key)
        sys.exit(1)

    if os.path.exists(args.certfile) and not args.overwrite:
        print("* ERR VAULT CERT UTIL *: %s already exists and --overwrite is not specified" % args.certfile)
        sys.exit(1)

    if os.path.exists(args.keyfile) and not args.overwrite:
        print("* ERR VAULT CERT UTIL *: %s already exists and --overwrite is not specified" % args.keyfile)
        sys.exit(1)


def main():
    print("* INF VAULT CERT UTIL *: cwd is %s" % os.getcwd())
    parser = get_parser()
    args, wrapped_args = parser.parse_known_args()
    validate_args(args)

    vcl = hvac.Client(url=args.vault_address,
                      token=args.vault_token if args.vault_token else None,
                      verify=args.pin_cacert if args.pin_cacert else args.verify,
                      cert=(
                          args.client_cert,
                          args.client_key
                      ) if args.client_cert else None)

    try:
        if args.client_cert:
            vcl.auth_tls()

        if args.vault_appid:
            vcl.auth_app_id(args.vault_appid, args.vault_userid)
    except RequestException as e:
        print("* ERR VAULT CERT UTIL *: Failure while authenticating to Vault. (%s)" % str(e))
        sys.exit(1)
    if not vcl.is_authenticated():
        print("* ERR VAULT CERT UTIL *: vaultgetcert was unable to authenticate with Vault, but no error occured "
              ":(.")
        sys.exit(1)

    with open(args.certfile, "wt", encoding="ascii") as certfile:
        with open(args.keyfile, "wt", encoding="ascii") as keyfile:
            os.chmod(args.keyfile, '0600')
            try:
                res = vcl.write(args.cert_key)
            except RequestException as e:
                print("* ERR VAULT WRAPPER *: Unable to read Vault path %s. (%s)" % (args.cert_key, str(e)))
                sys.exit(1)

            if "data" not in res or "certificate" not in res["data"] or "private_key" not in res["data"]:
                print("* ERR VAULT CERT UTIL *: Vault returned a value without the necessary fields "
                      "(data->certificate,private_key). Returned dict was:\n%s" %
                      str(res))
            certfile.write(res["data"]["certificate"])
            keyfile.write(res["data"]["keyfile"])

    print("* INF VAULT CERT UTIL *: the issued certificate and key have been stored in %s and %s" %
          (args.certfile, args.keyfile))
    print("*** Done.")
