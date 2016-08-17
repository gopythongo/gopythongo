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
              "Here is an example for how I use Vault to store the GnuPG package signature\n"
              "passphrase for GoPythonGo packages:\n"
              "\n"
              "Let's set up a read policy, assuming that you have already authenticated to\n"
              "Vault:\n"
              "\n"
              "    vault policy-write r_pkg_sign -\n"
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
              "    # Make sure you are authenticated with Vault, then run something like the\n"
              "    # following commands:\n"
              "    vault auth-enable app-id"
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
        description="Use this program as a replacement for the any binary that needs to read a passphrase from STDIN, "
                    "be it GnuPG or SSL. This was initially built for GoPythonGo/Aptly. It allows you to load a key "
                    "passphrase from Hashicorp Vault (https://vaultproject.io/), thereby increasing security on your "
                    "servers. To configure GoPythonGo specifically to use vault_wrapper, simply set "
                    "'--aptly-use-vault-wrapper' on your GoPythonGo command-line. All parameters not recognized by "
                    "vault_wrapper are passed directly to the wrapped program, so all other command-line options "
                    "work as expected. If you use '--mode=aptly' vault_wrapper will always append "
                    "'-passphrase-file /dev/stdin' to the final aptly command-line and send the passphrase twice "
                    "(for both signing operations).",
        prog="gopythongo.vault_Wrapper",
        args_for_setting_config_path=args_for_setting_config_path,
        config_arg_help_message="Use this path instead of the default (.gopythongo/vaultwrapper)",
        default_config_files=default_config_files
    )

    parser.add_argument("--wrap-program", dest="wrap_program", default=None, env_var="WRAP_PROGRAM",
                        help="Path to the executable to wrap and provide a passphrase to.")
    parser.add_argument("--address", dest="vault_address", default="https://vault.local:8200",
                        env_var="VAULT_URL", help="Vault URL")
    parser.add_argument("--wrap-mode", dest="wrap_mode", choices=["aptly", "stdin"], default="stdin",
                        help="Select a mode of operation. 'aptly' will append '-passphrase-file /dev/stdin' to the "
                             "wrapped program's parameters and output the passphrase twice, because aptly requires "
                             "that for package signing.")
    parser.add_argument("--read-key", dest="read_key", default=None, required=True,
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


def validate_args(args: configargparse.Namespace) -> None:
    if not args.vault_token:
        if not args.vault_appid or not args.vault_userid:
            print("* ERR VAULT WRAPPER *: You must specify an authentication method, so you must pass either "
                  "--token or --app-id and --user-id or set the VAULT_TOKEN, VAULT_APPID and VAULT_USERID environment "
                  "variables respectively. If you run GoPythonGo under sudo (e.g. for pbuilder), make sure your "
                  "build server environment variables also exist in the root shell, or build containers, or "
                  "whatever else you're using.")
            if args.vault_appid:
                print("* INF VAULT WRAPPER *: appid is set")
            if args.vault_userid:
                print("* INF VAULT WRAPPER *: userid is set")
            sys.exit(1)

    if args.vault_token:
        if args.vault_appid or args.vault_userid:
            print("* ERR VAULT WRAPPER *: Can't use app-id authentication with token authentication (--app-id/"
                  "--user-id and --token are mutually exclusive).")
            sys.exit(1)

    if args.wrap_program and (not os.path.exists(args.wrap_program) or not os.access(args.wrap_program, os.X_OK)):
        print("* ERR VAULT WRAPPER *: Wrapped executable %s doesn't exist or is not executable." % args.wrap_program)
        sys.exit(1)

    if args.client_cert and (not os.path.exists(args.client_cert) or not os.access(args.client_cert, os.R_OK)):
        print("* ERR VAULT WRAPPER *: %s File not found or no read privileges" % args.client_cert)

    if args.client_key and (not os.path.exists(args.client_key) or not os.access(args.client_key, os.R_OK)):
        print("* ERR VAULT WRAPPER *: %s File not found or no read privileges" % args.client_key)


def main() -> None:
    print("* INF VAULT WRAPPER *: cwd is %s" % os.getcwd())
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
        print("* ERR VAULT WRAPPER *: Failure while authenticating to Vault. (%s)" % str(e))
        sys.exit(1)
    if not vcl.is_authenticated():
        print("* ERR VAULT WRAPPER *: aptly_vault_wrapper was unable to authenticate with Vault, but no error occured "
              ":(.")
        sys.exit(1)

    try:
        res = vcl.read(args.read_key)
    except RequestException as e:
        print("* ERR VAULT WRAPPER *: Unable to read Vault path %s. (%s)" % (args.read_key, str(e)))
        sys.exit(1)

    if "data" not in res or "value" not in res["data"]:
        print("* ERR VAULT WRAPPER *: Vault returned a value without the necessary fields (data->value). Returned "
              "dict was:\n%s" %
              res)

    passphrase = res['data']['value']

    if args.wrap_mode == "aptly":
        cmdline = [args.wrap_program, "--passphrase-file", "/dev/stdin"] + wrapped_args
    else:
        cmdline = [args.wrap_program] + wrapped_args

    with subprocess.Popen(cmdline, universal_newlines=True, stdin=subprocess.PIPE, bufsize=0, stdout=sys.stdout,
                          stderr=sys.stderr) as proc:
        if args.wrap_mode == "aptly":
            proc.communicate(input="%s\n%s\n" % (passphrase, passphrase))
        else:
            proc.communicate(input="%s\n" % passphrase)

    if proc.returncode != 0:
        print("* ERR VAULT WRAPPER *: Call to aptly failed with exit code %s." % proc.returncode)
        sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
