# -* encoding: utf-8 *-
import configargparse
import hvac

from typing import List


args_for_setting_config_path = ["-c", "--config"]  # type: List[str]
default_config_files = [".gopythongo/vault"]  # type: List[str]


def get_parser() -> configargparse.ArgumentParser:
    parser = configargparse.ArgumentParser(
        description="Use this program as a replacement for the gnupg binary with GoPythonGo/Aptly. This will allow you "
                    "to load the gpg key passphrase for a package signing operation from Hashicorp Vault "
                    "(https://vaultproject.io/), thereby increasing security on your build servers. To configure "
                    "GoPythonGo to use the gopythongo.gpg_vault_wrapper, simply set '--use-gpg' on your GoPythonGo "
                    "command-line to this program.",
        prog="gopythongo.gpg_vault_Wrapper",
        args_for_setting_config_path=args_for_setting_config_path,
        config_arg_help_message="Use this path instead of the default (.gopythongo/vault)",
        default_config_files=default_config_files
    )

    parser.add_argument("--wrap-gpg", dest="wrap_gpg", default="/usr/bin/gpg", env_var="WRAP_GPG",
                        help="Path to the real GnuPG executable.")
    parser.add_argument("--address", dest="vault_address", default="https://127.0.0.1:8200",
                        env_var="VAULT_URL", help="Vault URL")
    parser.add_argument("--read-key", dest="read_key", default="/secrets/gpg/passphrase",
                        env_var="VAULT_READ_KEY", help="The key path to read from Vault. The value found there will "
                                                       "be used as the passphrase.")

    gp_auth = parser.add_argument_group("Vault authentication options")
    gp_auth.add_argument("--token", dest="vault_token", env_var="VAULT_TOKEN",
                         help="A Vault access token with a valid lease. This is one way of authenticating the wrapper "
                              "to Vault.")
    gp_auth.add_argument("--app-id", dest="vault_appid", env_var="VAULT_APPID",
                         help="")
    return parser


def main() -> None:
    parser = get_parser()
    args, _ = parser.parse_known_args()


if __name__ == "__main__":
    main()
