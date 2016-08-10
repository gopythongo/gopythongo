# -* encoding: utf-8 *-
import os
import subprocess

import configargparse
import hvac

from typing import List, Sequence, Iterable, Union, Any

import sys

from requests.exceptions import RequestException

args_for_setting_config_path = ["--aptly-wrapper-config"]  # type: List[str]
default_config_files = [".gopythongo/aptlywrapper"]  # type: List[str]


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
        print("Vault Integration\n"
              "=================\n"
              "\n"
              "When signing packages, GoPythonGo/Aptly must know the passphrase to use for GPG,\n"
              "especially when GoPythonGo is invoked on a build server without user\n"
              "interaction. A good way to manage secret information such as GPG passphrases for\n"
              "automated jobs or SSL keys is Hashicorp's Vault (https://vaultproject.io/).\n"
              "Using aptly_vault_wrapper as a replacement for the aptly executable allows you\n"
              "to query Vault for the GPG passphrase to use when signing packages.\n"
              "\n"
              "Once you have a configured, initialized and unsealed Vault installation in your\n"
              "network, you must set up a policy for aptly_vault_wrapper to use and define a\n"
              "way for aptly_vault_wrapper to authenticate. Currently aptly_vault_wrapper\n"
              "allows you to pass in a Vault auth token or use the app-id authentication\n"
              "backend.\n"
              "\n"
              "Let's set up the policy, assuming that you have already authenticated to Vault:\n"
              "\n"
              "    cat | vault policy-write r_pkg_sign -\n"
              "path \"secret/gpg/package_sign_passphrase\" {\n"
              "    capabilities = [\"read\"]\n"
              "}\n"
              "\n"
              "Then store the passphrase there:\n"
              "\n"
              "    vault write secret/gpg/package_sign_passphrase value=-\n"
              "[send passphrase from stdin so as to not save it in your shell history!]\n"
              "\n"
              "And finally set up app-id for aptly_vault_wrapper. Make sure you set cidr_block\n"
              "to an appropriate value for your network:\n"
              "\n"
              "    APPID=$(python3 -c \"import uuid; print(str(uuid.uuid4()), end='')\")\n"
              "    vault write auth/app-id/map/app-id/$APPID value=r_pkg_sign \\\n"
              "        display_name=aptly_vault_wrapper\n"
              "    USERID=$(python3 -c \"import uuid; print(str(uuid.uuid4()), end='')\")\n"
              "    vault write auth/app-id/map/user-id/$USERID value=$APPID \\\n"
              "        cidr_block=192.168.56.0/24\n"
              "    echo 'App-id (put this in your .gopythongo settings):'\n"
              "    echo $APPID\n"
              "\n"
              "    echo 'User-id (put this in the VAULT_USERID environment variable on your'\n"
              "    echo 'build server, or in your build job config):'\n"
              "    echo $USERID\n"
              "\n"
              "Security notice: THe documentation only states this implicitly, but you should\n"
              "only use 'hard to guess' UUIDs here. On most systems Python uses os.urandom, so\n"
              "this should be fine, but it doesn't hurt to check.\n")
        parser.exit(0)


def get_parser() -> configargparse.ArgumentParser:
    parser = configargparse.ArgumentParser(
        description="Use this program as a replacement for the aptly binary with GoPythonGo/Aptly. This will allow you "
                    "to load the gnupg key passphrase for a package signing operation from Hashicorp Vault "
                    "(https://vaultproject.io/), thereby increasing security on your build servers. To configure "
                    "GoPythonGo to use aptly_vault_wrapper, simply set '--aptly-use-vault-wrapper' on your GoPythonGo "
                    "command-line. All parameters not recognized by aptly_vault_wrapper are passed "
                    "directly to aptly, so all other aptly options still work. aptly_vault_wrapper will always append "
                    "'-passphrase-file /dev/stdin' to the final aptly command-line and send the passphrase twice "
                    "(for both signing operations).",
        prog="gopythongo.aptly_vault_Wrapper",
        args_for_setting_config_path=args_for_setting_config_path,
        config_arg_help_message="Use this path instead of the default (.gopythongo/aptlywrapper)",
        default_config_files=default_config_files
    )

    parser.add_argument("--wrap-aptly", dest="wrap_aptly", default="/usr/bin/aptly", env_var="WRAP_APTLY",
                        help="Path to the real Aptly executable.")
    parser.add_argument("--address", dest="vault_address", default="https://vault.local:8200",
                        env_var="VAULT_URL", help="Vault URL")
    parser.add_argument("--read-key", dest="read_key", default="/secret/gpg/package_sign_passphrase",
                        env_var="VAULT_READ_KEY",
                        help="The key path to read from Vault. The value found there will be used as the passphrase.")
    parser.add_argument("--help-policies", action=HelpAction,
                        help="Show additional information about how to set up Vault for using aptly_vault_wrapper.")

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
    return parser


def validate_args(args: configargparse.Namespace):
    if not args.vault_token:
        if not args.vault_appid or not args.vault_userid:
            print("* ERROR: You must specify an authentication method, so you must pass either --token or --app-id and "
                  "--user-id or set the VAULT_TOKEN, VAULT_APPID and VAULT_USERID environment variables respectively.")
            sys.exit(1)

    if args.vault_token:
        if args.vault_appid or args.vault_userid:
            print("* ERROR: Can't use app-id authentication with token authentication (--app-id/--user-id and "
                  "--token are mutually exclusive).")
            sys.exit(1)

    if args.wrap_aptly and (not os.path.exists(args.wrap_aptly) or not os.access(args.wrap_aptly, os.X_OK)):
        print("* ERROR: Aptly executable %s doesn't exist or is not executable." % args.wrap_gpg)
        sys.exit(1)

    if args.client_cert and (not os.path.exists(args.client_cert) or not os.access(args.client_cert, os.R_OK)):
        print("* ERROR: %s File not found or no read privileges" % args.client_cert)

    if args.client_key and (not os.path.exists(args.client_key) or not os.access(args.client_key, os.R_OK)):
        print("* ERROR: %s File not found or no read privileges" % args.client_key)


def main() -> None:
    parser = get_parser()
    args, aptly_args = parser.parse_known_args()
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
        print("* ERROR: Failure while authenticating to Vault. (%s)" % str(e))
        sys.exit(1)
    if not vcl.is_authenticated():
        print("* ERROR: aptly_vault_wrapper was unable to authenticate with Vault, but no error occured :(.")
        sys.exit(1)

    try:
        res = vcl.read(args.read_key)
    except RequestException as e:
        print("* ERROR: Unable to read Vault path %s. (%s)" % (args.read_key, str(e)))
        sys.exit(1)

    if "data" not in res or "value" not in res["data"]:
        print("* ERROR: Vault returned a value without the necessary fields (data->value). Returned dict was:\n%s" %
              res)

    passphrase = res['data']['value']

    aptly_cmdline = [args.wrap_aptly, "--passphrase-file", "/dev/stdin"] + aptly_args
    subprocess.call(aptly_cmdline, input=("%s\n%s\n" % (passphrase, passphrase)).encode("utf-8"),
                    universal_newlines=True, stdout=sys.stdout, stderr=sys.stderr)


if __name__ == "__main__":
    main()
