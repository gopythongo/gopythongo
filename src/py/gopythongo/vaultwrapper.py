# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import subprocess

import configargparse
import hvac

from typing import List, Sequence, Iterable, Union, Any

import sys

from gopythongo.main import DebugConfigAction
from requests.exceptions import RequestException
from typing import Dict

args_for_setting_config_path = ["--vault-wrapper-config"]  # type: List[str]
default_config_files = [".gopythongo/vaultwrapper"]  # type: List[str]


def _out(*args: Any, **kwargs: Any) -> None:
    if "file" not in kwargs:
        kwargs["file"] = sys.stderr
    print(*args, **kwargs)


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
              "    vault auth-enable app-id\n"
              "    APPID=$(python3 -c \"import uuid; print(str(uuid.uuid4()), end='')\")\n"
              "    vault write auth/app-id/map/app-id/$APPID value=r_pkg_sign \\\n"
              "        display_name=vaultwrapper\n"
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
        prog="gopythongo.vaultwrapper",
        args_for_setting_config_path=args_for_setting_config_path,
        config_arg_help_message="Use this path instead of the default (.gopythongo/vaultwrapper)",
        default_config_files=default_config_files
    )

    parser.add_argument("--wrap-program", dest="wrap_program", default=None, env_var="VAULTWRAPPER_PROGRAM",
                        help="Path to the executable to wrap and provide a passphrase to.")
    parser.add_argument("--address", dest="vault_address", default="https://vault.local:8200",
                        env_var="VAULT_URL", help="Vault URL")
    parser.add_argument("--wrap-mode", dest="wrap_mode", choices=["aptly", "stdin"], default="stdin",
                        help="Select a mode of operation. 'aptly' will append '-passphrase-file /dev/stdin' to the "
                             "wrapped program's parameters and output the passphrase twice, because aptly requires "
                             "that for package signing.")
    parser.add_argument("--read-path", dest="read_path", default=None, required=True,
                        env_var="VAULTWRAPPER_READ_PATH",
                        help="The path to read from Vault. By default, vaultwrapper will look for a key 'passphrase' "
                             "under this path (see --field).")
    parser.add_argument("--field", dest="read_field", default="passphrase", env_var="VAULTWRAPPER_FIELD",
                        help="The key to read from the specified path. (Default: 'passphrase')")
    parser.add_argument("--help-policies", action=HelpAction,
                        help="Show additional information about how to set up Vault for using vaultwrapper.")
    parser.add_argument("--debug-config", action=DebugConfigAction)
    parser.add_argument("--gpg-homedir", dest="gpg_homedir", default=None,
                        help="Set $GNUPGHOME before executing the wrapped program, which helps to run aptly with "
                             "gpg2.")

    gp_https = parser.add_argument_group("HTTPS options")
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
    gp_auth.add_argument("--client-cert", dest="client_cert", default=None, env_var="VAULT_CLIENTCERT",
                         help="Use a HTTPS client certificate to connect.")
    gp_auth.add_argument("--client-key", dest="client_key", default=None, env_var="VAULT_CLIENTKEY",
                         help="Set the HTTPS client certificate private key.")

    return parser


def validate_args(args: configargparse.Namespace) -> None:
    if args.vault_token:
        pass
    elif args.vault_appid and args.vault_userid:
        pass
    elif args.client_cert and args.client_key:
        pass
    else:
        _out("* ERR VAULT WRAPPER *: You must specify an authentication method, so you must pass either "
             "--token or --app-id and --user-id or --client-cert and --client-key or set the VAULT_TOKEN, "
             "VAULT_APPID and VAULT_USERID environment variables respectively. If you run GoPythonGo under "
             "sudo (e.g. for pbuilder), make sure your build server environment variables also exist in the "
             "root shell, or build containers, or whatever else you're using.")
        if args.vault_appid:
            _out("* INF VAULT WRAPPER *: appid is set")
        if args.vault_userid:
            _out("* INF VAULT WRAPPER *: userid is set")
        if args.client_cert:
            _out("* INF VAULT WRAPPER *: client_cert is set")
        if args.client_key:
            _out("* INF VAULT WRAPPER *: client_key is set")
        sys.exit(1)

    if not args.wrap_program:
        _out("* ERR VAULT WRAPPER *: You must specify an executable for vaultwrapper to wrap")
        sys.exit(1)

    if args.wrap_program and (not os.path.exists(args.wrap_program) or not os.access(args.wrap_program, os.X_OK)):
        _out("* ERR VAULT WRAPPER *: Wrapped executable %s doesn't exist or is not executable." % args.wrap_program)
        sys.exit(1)

    if args.client_cert and (not os.path.exists(args.client_cert) or not os.access(args.client_cert, os.R_OK)):
        _out("* ERR VAULT WRAPPER *: %s File not found or no read privileges" % args.client_cert)
        sys.exit(1)

    if args.client_key and (not os.path.exists(args.client_key) or not os.access(args.client_key, os.R_OK)):
        _out("* ERR VAULT WRAPPER *: %s File not found or no read privileges" % args.client_key)
        sys.exit(1)


def main() -> None:
    _out("* INF VAULT WRAPPER *: cwd is %s" % os.getcwd())
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

    if not vcl.is_authenticated():  # client is authenticated if we have a valid token
        try:
            if args.client_cert:
                vcl.auth_tls()

            if args.vault_appid:
                vcl.auth_app_id(args.vault_appid, args.vault_userid)
        except RequestException as e:
            _out("* ERR VAULT WRAPPER *: Failure while authenticating to Vault. (%s)" % str(e))
            sys.exit(1)
        if not vcl.is_authenticated():
            _out("* ERR VAULT WRAPPER *: vaultwrapper was unable to authenticate with Vault, but no error occured "
                 ":(.")
            sys.exit(1)

    try:
        res = vcl.read(args.read_path)
    except RequestException as e:
        _out("* ERR VAULT WRAPPER *: Unable to read Vault path %s. (%s)" % (args.read_path, str(e)))
        sys.exit(1)

    if res is None or "data" not in res or args.read_field not in res["data"]:
        _out("* ERR VAULT WRAPPER *: Vault returned a value without the necessary fields (data->%s). Returned "
             "dict for path %s was:\n%s" %
             (args.read_field, args.read_path, str(res)))
        sys.exit(1)

    passphrase = res['data'][args.read_field]

    if args.wrap_mode == "aptly":
        cmdline = [args.wrap_program, "-passphrase-file", "/dev/stdin"] + wrapped_args
    else:
        cmdline = [args.wrap_program] + wrapped_args

    modenv = {}  # type: Dict[str, str]
    if args.gpg_homedir:
        modenv = {"GNUPGHOME": args.gpg_homedir}

    with subprocess.Popen(cmdline, universal_newlines=True, stdin=subprocess.PIPE, bufsize=0, stdout=sys.stdout,
                          stderr=sys.stderr, env=dict(os.environ, **modenv)) as proc:
        if args.wrap_mode == "aptly":
            proc.communicate(input="%s\n%s\n" % (passphrase, passphrase))
        else:
            proc.communicate(input="%s\n" % passphrase)

    if proc.returncode != 0:
        _out("* ERR VAULT WRAPPER *: Call to aptly failed with exit code %s." % proc.returncode)
        sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
