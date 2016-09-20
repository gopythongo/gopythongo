# -* encoding: utf-8 *-
import functools
import os
import subprocess
import sys
import hvac
import configargparse

from typing import Dict, Sequence, Iterable, Union, Any, cast, TextIO

from OpenSSL import crypto
from gopythongo.main import DebugConfigAction
from requests.exceptions import RequestException


out_target = sys.stdout
umask_cur = os.umask(0o022)
os.umask(umask_cur)


def _out(*args: Any, **kwargs: Any) -> None:
    if "file" not in kwargs:
        kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def _result_output(envvar: str, value: str):
    print("%s=%s" % (envvar, value,), file=out_target)


def _result_envdir(envdir: str, envvar: str, value: str):
    fn = os.path.join(envdir, envvar)
    _out("writing %s" % fn)
    with open(fn, mode="wt", encoding="utf-8") as envf:
        envf.write(value)

_result = _result_output


def _get_masked_mode(mode: Union[int, str]) -> int:
    if isinstance(mode, str):
        m = int(mode, base=8)
    else:
        m = mode
    return (0o777 ^ umask_cur) & m


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
              "Continuous Integration (CD) build, you can create client credentials for\n"
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
              "vaultgetcert can also output environment variable key/value pairs and create\n"
              "multiple certificate chains for cross-signed trust paths, allowing you to\n"
              "centralize secret management as described in the GoPythonGo process "
              "documentation.\n"
              "\n"
              "Here is a cheatsheet for setting up a PKI endpoint in Vault:\n"
              "\n"
              "# Mount one PKI backend per environment and/or application that gets its own\n"
              "# builds on this server and allow builds to remain valid for 1 year (tune to\n"
              "# your specifications). Application CAs are better suited to Vault as it binds\n"
              "# roles to CAs. Environment CAs are better suited to some servers like Postgres\n"
              "# as they bind roles to CNs. Using vaultgetcert you can also easily use\n"
              "# cross-signed intermediate CAs and use both approaches.\n"
              "vault mount -path=pki-YourApplication -default-lease-ttl=8760h \\\n"
              "    -max-lease-ttl=8760h pki\n"
              "\n"
              "# generate an intermediate CA with a 2048 bit key (default)\n"
              "vault write pki-YourApplication/intermediate/generate/internal \\\n"
              "    common_name=\"(YourApplication) Build CA X1\"\n"
              "\n"
              "# Sign the intermediate CA using your private CA\n"
              "# then write the certificate back to the Vault store\n"
              "vault write pki-YourApplication/intermediate/set-signed certificate=@cacert.pem\n"
              "\n"
              "# Now this CA certificate should be installed on the relevant servers, e.g. in\n"
              "# Postgres ssl_ca_cert. You can also use the root certificate with a trustchain\n"
              "# in the client certificate.\n"
              "vault write pki-YourApplication/roles/build ttl=8760h allow_localhost=false \\\n"
              "    allow_ip_sans=false server_flag=false client_flag=true \\\n"
              "    allow_any_name=true key_type=rsa\n"
              "\n"
              "# Request a build certificate for a build.\n"
              "# This is basically what vaultgetcert does! So instead of running this command\n"
              "# use vaultgetcert :)\n"
              "# We \"hack\" the git hash into a domain name SAN because Vault currently\n"
              "# doesn't support freetext SANs.\n"
              "vault write pki-YourApplication/issue/build common_name=\"yourapp\" \\\n"
              "    alt_names=\"024572834273498734.git\" exclude_cn_from_sans=true\n"
              "\n"
              "# Set everything up to authenticate to Vault using these certs. For example:\n"
              "vault auth-enable cert\n"
              "vault mount -path=db-YourApplication postgresql\n"
              "vault write db-YourApplication/config/lease lease=96h lease_max=96h\n"
              "vault write db-YourApplication/config/connection connection_url=-\n"
              "postgresql://vaultadmin:(PASSWORD)@postgresql.local:5432/postgres\n"
              "\n"
              "vault write db-YourApplication/roles/fullaccess sql=-\n"
              "    CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}'\n"
              "        VALID UNTIL '{{expiration}}';\n"
              "    GRANT ALL PRIVILEGES ON DATABASE YourApplication TO \"{{name}}\";\n"
              "\n"
              "vault policy-write yourapp_rights -\n"
              "path \"db-YourApplication/creds/fullaccess\" {\n"
              "    capabilities = [\"read\"]\n"
              "}\n"
              "\n"
              "vault write auth/cert/certs/YourApplication \\\n"
              "    display_name=yourapp \\\n"
              "    policies=yourapp_rights \\\n"
              "    certificate=@cacert.pem \\\n"
              "    ttl=3600\n")
        parser.exit(0)


def get_parser() -> configargparse.ArgumentParser:
    parser = configargparse.ArgumentParser(
        description="This is a little helper tool that contacts a Vault server to issue a SSL client "
                    "certificate and save its X.509 certificate and private key to local files. Use "
                    "--help-verbose to learn more. vaultgetcert expects everything to be PEM encoded. "
                    "It cannot convert between different formats.",
        prog="gopythongo.vaultgetcert",
        args_for_setting_config_path=["-c"],
        config_arg_help_message="Use this path instead of the default (.gopythongo/vaultwrapper)",
        default_config_files=[".gopythongo/vaultgetcert",]
    )

    parser.add_argument("-o", "--output", dest="output", default=None, env_var="VGC_OUTPUT",
                        help="Direct output to this file or folder (when in envdir mode). (default: stdout)")
    parser.add_argument("--envdir", dest="envdir_mode", default=False, action="store_true", env_var="VGC_ENVDIR",
                        help="When this is set, vaultgetcert will write each environment variable setting into its "
                             "own file, creating a DJB daemontools compatible envdir.")
    parser.add_argument("--address", dest="vault_address", default="https://vault.local:8200",
                        env_var="VGC_VAULT_URL",
                        help="Vault API base URL (default: https://vault.local:8200/). ")
    parser.add_argument("--vault-pki", dest="vault_pki", default=None, required=True,
                        env_var="VGC_VAULT_PKI",
                        help="The PKI backend path to issue a certificate from Vault (e.g. 'pki/issue/[role]').")
    parser.add_argument("--subject-alt-names", dest="subject_alt_names", env_var="VGC_SUBJECT_ALTNAME",
                        default=None,
                        help="alt_names parameter to pass to Vault for the issued certificate. (Use a comma-separated "
                             "list if you want to specify more than one.)")
    parser.add_argument("--common-name", dest="common_name", env_var="VGC_COMMON_NAME", default=None, required=True,
                        help="The CN to pass to Vault for the issued certificate.")
    parser.add_argument("--include-cn-in-sans", dest="include_cn_in_sans", env_var="VGC_INCLUDE_CN_IN_SANS",
                        default=False, action="store_true",
                        help="Set this if you want the value of --common-name to also show up in the issued "
                             "certificate's SANs.")
    parser.add_argument("--certfile-out", dest="certfile", env_var="VGC_CERTFILE_OUT", required=True,
                        help="Path of the file where the generated certificate will be stored. ")
    parser.add_argument("--keyfile-out", dest="keyfile", env_var="VGC_KEYFILE_OUT", required=True,
                        help="Path of the file where the generated private key will be stored. Permissions for this "
                             "file will be set to 600.")
    parser.add_argument("--certchain-out", dest="certchain", env_var="VGC_CERTCHAIN_OUT", default=None,
                        help="Save the issuer CA certificate, which is likely the intermediate CA that you need to "
                             "provide in the certificate chain.")
    parser.add_argument("--overwrite", dest="overwrite", env_var="VGC_OVERWRITE", default=False, action="store_true",
                        help="When set, this program will overwrite existing certificates and keys on disk. ")
    parser.add_argument("--help-verbose", action=HelpAction,
                        help="Show additional information about how to set up Vault for using vaultgetcert.")
    parser.add_argument("--debug-config", action=DebugConfigAction)

    gp_xsign = parser.add_argument_group("Handling cross-signing CAs")
    gp_xsign.add_argument("--xsign-cacert", dest="xsigners", default=[], action="append", env_var="VGC_XSIGN_CACERT",
                          help="Can be set multiple times. The argument must be in the form 'bundlename=certificate'. "
                               "For each certificate specified, vaultgetcert will verify that it uses the same public "
                               "key as the issuer certificate returned by Vault. It will then create a bundle "
                               "(concatenated PEM file) for each xsign-cacert with the specified name. MUST be used "
                               "together with --xsign-bundle-path. You can specify an absolute path for bundlename in "
                               "which case --xsign-bundle-path will not be used for that bundlename.")
    gp_xsign.add_argument("--issuer-bundle", dest="issuer_bundle", default=None,
                          help="The argument for this is the bundlename for the issuer certificate returned by Vault. "
                               "That bundlename will be handled like --xsign-cacert bundlenames. It can also be used "
                               "in --output-bundle-envvar, thereby allowing you to use whichever CA Vault returns like "
                               "any other well-known CA.")
    gp_xsign.add_argument("--xsign-bundle-path", dest="bundlepath", default=None, env_var="VGC_XSIGN_BUNDLE_PATH",
                          help="A folder where all of the generated files without absolute paths from specified "
                               "--xsign-cacert parameters will be stored. Existing bundles will be overwritten.")
    gp_xsign.add_argument("--output-bundle-envvar", dest="bundle_envvars", default=[], action="append",
                          env_var="VGC_OUTPUT_BUNDLE_ENVVAR",
                          help="Can be specified multiple times. The argument must be in the form "
                               "'envvar=bundlename[:altpath]' (altpath is optional). "
                               "For each envvar specified vaultgetcert will output 'envvar=bundlepath' to stdout. If "
                               "you specify 'altpath', 'altpath' will replace the FULL path in bundlepath. The "
                               "filename will stay the same. This output is meant to be used as configuration "
                               "environment variables for your program and can be shipped, for example, for usage in "
                               "/etc/default.")
    gp_xsign.add_argument("--output-key-envvar", dest="key_envvars", default=[], action="append",
                          env_var="VGC_OUTPUT_KEY_ENVVAR",
                          help="Can be specified multiple times. Output one or more key/value pairs to stdout in the "
                               "form 'envvar=keyfile' where 'keyfile' is the file specified by --keyfile-out. Each "
                               "argument should be formatted like 'envvar[:altpath]' where 'altpath' is optional. If "
                               "'altpath' is specified, the keyfile's path will be replaced by 'altpath' in the "
                               "output.")

    gp_filemode = parser.add_argument_group("File mode options")
    gp_filemode.add_argument("--mode-mkdir-output", dest="mode_output_dir", default="0o755",
                             env_var="VGC_MODE_MKDIR_OUTPUT",
                             help="If the output folder for the environment variable configuration (--output) doesn't "
                                  "exist yet, create it with these permissions (will be umasked). (default: 0o755)")
    gp_filemode.add_argument("--mode-mkdir-certs", dest="mode_certs_dir", default="0o755",
                             env_var="VGC_MODE_MKDIR_CERTS",
                             help="If the output folders for certificates and bundles (--certfile-out, "
                                  "--certchain-out, --xsign-bundle-path) doesn't exist yet, create them with these "
                                  "permissions (will be umasked). (default: 0o755)")
    gp_filemode.add_argument("--mode-mkdir-key", dest="mode_key_dir", default="0o700",
                             env_var="VGC_MODE_MKDIR_KEY",
                             help="If the output folder for the private key (--keyfile-out) doesn't exist yet, "
                                  "create it with these permissions (will be umasked). (default: 0o700)")
    gp_filemode.add_argument("--mode-file-output", dest="mode_output_file", default="0o644",
                             env_var="VGC_MODE_FILE_OUTPUT",
                             help="Create the output file (--output) with these permissions (will be umasked). "
                                  "(default: 0o644)")
    gp_filemode.add_argument("--mode-certbundles", dest="mode_certbundle_files", default="0o644",
                             env_var="VGC_MODE_CERTBUNDLES",
                             help="Create the certbundle files (--xsign-cacert) with these permissions (will be "
                                  "umasked). (default: 0o644)")
    gp_filemode.add_argument("--mode-keyfile", dest="mode_key_file", default="0o600",
                             env_var="VGC_MODE_KEYFILE",
                             help="Create the private key file (--keyfile-out) with these permissions (will be "
                                  "umasked). (default: 0o600)")

    gp_https = parser.add_argument_group("HTTPS options")
    gp_https.add_argument("--pin-cacert", dest="pin_cacert", default="/etc/ssl/certs/ca-certificates.crt",
                          env_var="VGC_VAULT_CACERT",
                          help="Set the CA certificate for Vault (i.e. the server certificate MUST be signed by a CA "
                               "in this file). The file should contain a list of CA certificates. The default is the "
                               "location of the Debian Linux CA bundle (Default: '/etc/ssl/certs/ca-certificates.crt')")
    gp_https.add_argument("--tls-skip-verify", dest="verify", env_var="VGC_SSL_SKIP_VERIFY", default=True,
                          action="store_false",
                          help="Skip SSL verification (only use this during debugging or development!)")

    gp_auth = parser.add_argument_group("Vault authentication options")
    gp_auth.add_argument("--token", dest="vault_token", env_var="VAULT_TOKEN", default=None,
                         help="A Vault access token with a valid lease. This is one way of authenticating the wrapper "
                              "to Vault. This is mutually exclusive with --app-id/--user-id. ")
    gp_auth.add_argument("--app-id", dest="vault_appid", env_var="VAULT_APPID", default=None,
                         help="Set the app-id for Vault app-id authentication.")
    gp_auth.add_argument("--user-id", dest="vault_userid", env_var="VAULT_USERID", default=None,
                         help="Set the user-id for Vault app-id authentication.")
    gp_auth.add_argument("--client-cert", dest="client_cert", default=None, env_var="VAULT_CLIENTCERT",
                         help="Use a HTTPS client certificate to connect.")
    gp_auth.add_argument("--client-key", dest="client_key", default=None, env_var="VAULT_CLIENTKEY",
                         help="Set the HTTPS client certificate private key.")

    gp_git = parser.add_argument_group("Git integration")
    gp_git.add_argument("--use-git", dest="git_binary", default="/usr/bin/git", env_var="VGC_GIT",
                        help="Specify an alternate git binary to call for git integration. (default: /usr/bin/git)")
    gp_git.add_argument("--git-include-commit-san", dest="git_include_commit_san", default=".", action="store_true",
                        env_var="VGC_INCLUDE_COMMIT_SAN",
                        help="If 'git rev-parse HEAD' returns a commit hash, add a certificate SAN called "
                             "'[commithash].git'.")

    return parser


xsign_bundles = {}  # type: Dict[str, str]
bundle_vars = {}  # type: Dict[str, Dict[str, str]]


def validate_args(args: configargparse.Namespace) -> None:
    if args.vault_token:
        pass
    elif args.vault_appid and args.vault_userid:
        pass
    elif args.client_cert and args.client_key:
        pass
    else:
        _out("* ERR VAULT CERT UTIL *: You must specify an authentication method, so you must pass either "
             "--token or --app-id and --user-id or --client-cert and --client-key or set the VAULT_TOKEN, "
             "VAULT_APPID and VAULT_USERID environment variables respectively. If you run GoPythonGo under "
             "sudo (e.g. for pbuilder), make sure your build server environment variables also exist in the "
             "root shell, or build containers, or whatever else you're using.")
        if args.vault_appid:
            _out("* INF VAULT CERT UTIL *: appid is set")
        if args.vault_userid:
            _out("* INF VAULT CERT UTIL *: userid is set")
        if args.client_cert:
            _out("* INF VAULT CERT UTIL *: client_cert is set")
        if args.client_key:
            _out("* INF VAULT CERT UTIL *: client_key is set")
        sys.exit(1)

    if args.client_cert and (not os.path.exists(args.client_cert) or not os.access(args.client_cert, os.R_OK)):
        _out("* ERR VAULT CERT UTIL *: %s File not found or no read privileges" % args.client_cert)
        sys.exit(1)

    if args.client_key and (not os.path.exists(args.client_key) or not os.access(args.client_key, os.R_OK)):
        _out("* ERR VAULT CERT UTIL *: %s File not found or no read privileges" % args.client_key)
        sys.exit(1)

    if os.path.exists(args.certfile) and not args.overwrite:
        _out("* ERR VAULT CERT UTIL *: %s already exists and --overwrite is not specified" % args.certfile)
        sys.exit(1)

    if os.path.exists(os.path.dirname(args.certfile)) and not os.access(os.path.dirname(args.certfile), os.W_OK):
        _out("* ERR VAULT CERT UTIL *: %s already exists and is not writable (--certfile-out)" %
             os.path.dirname(args.certfile))
        sys.exit(1)

    if os.path.exists(args.keyfile) and not args.overwrite:
        _out("* ERR VAULT CERT UTIL *: %s already exists and --overwrite is not specified" % args.keyfile)
        sys.exit(1)

    if os.path.exists(os.path.dirname(args.keyfile)) and not os.access(os.path.dirname(args.keyfile), os.W_OK):
        _out("* ERR VAULT CERT UTIL *: %s already exists and is not writable (--keyfile-out)" %
             os.path.dirname(args.keyfile))
        sys.exit(1)

    if args.git_include_commit_san and (not os.path.exists(args.git_binary) or not os.access(args.git_binary, os.X_OK)):
        _out("* ERR VAULT CERT UTIL *: --git-include-commit-san is set, but Git binary %s does not exist or is not "
             "executable" % args.git_binary)
        sys.exit(1)

    for xcertspec in args.xsigners:
        if "=" not in xcertspec:
            _out("* ERR VAULT CERT UTIL *: each --xsign-cacert argument must be formed as 'bundlename=certificate'. "
                 "%s is not." % xcertspec)
        bundlename, xcert = xcertspec.split("=", 1)
        if bundlename not in xsign_bundles.keys():
            xsign_bundles[bundlename] = xcert
        else:
            _out("* ERR VAULT CERT UTIL *: duplicate xsigner bundle name %s (from 1:%s and 2:%s=%s)" %
                 (bundlename, xcertspec, bundlename, xsign_bundles[bundlename]))
        if not os.path.exists(xcert) or not os.access(xcert, os.R_OK):
            _out("* ERR VAULT CERT UTIL *: %s does not exist or is not readable (from %s)" % (xcert, xcertspec))
            sys.exit(1)

    if args.issuer_bundle:
        xsign_bundles[args.issuer_bundle] = None

    if args.bundlepath:
        if os.path.exists(args.bundlepath) and not os.access(args.bundlepath, os.W_OK):
            _out("* ERR VAULT CERT UTIL *: %s is not writable" % args.bundlepath)

    for benvspec in args.bundle_envvars:
        if "=" not in benvspec:
            _out("* ERR VAULT CERT UTIL *: each --output-bundle-envvar must be formed as 'envvar=bundlename[:altpath]' "
                 "with altpath being optional. %s is not." % benvspec)
        envvar, bundlespec = benvspec.split("=", 1)
        if ":" in bundlespec:
            bundleref, altpath = bundlespec.split(":", 1)
        else:
            bundleref, altpath = bundlespec, None

        if bundleref not in xsign_bundles.keys():
            _out("* ERR VAULT CERT UTIL *: --output-bundle-envvar argument %s references a bundle name %s which has "
                 "not been specified as an argument to --xsign-cacert." % (benvspec, bundleref))

        bundle_vars[bundleref] = {
            "envvar": envvar,
            "altpath": altpath,
        }

    for perms in [args.mode_output_dir, args.mode_certs_dir, args.mode_key_dir, args.mode_output_file,
                  args.mode_certbundle_files, args.mode_key_file]:
        try:
            int(perms, base=8)
        except ValueError:
            _out("* ERR VAULT CERT UTIL *: %s is not a vaild permission string (must be octal unix file/folder "
                 "permissions" % perms)
            sys.exit(1)

    if args.envdir_mode and os.path.exists(args.output) and not os.path.isdir(args.output):
        _out("* ERR VAULT CERT UTIL *: %s already exists and is not a directory. --envdir requires the output path "
             "to be a directory or not exist.")


def main() -> None:
    global out_target, _result

    _out("* INF VAULT CERT UTIL *: cwd is %s" % os.getcwd())
    parser = get_parser()
    args = parser.parse_args()
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
        _out("* ERR VAULT CERT UTIL *: Failure while authenticating to Vault. (%s)" % str(e))
        sys.exit(1)
    if not vcl.is_authenticated():
        _out("* ERR VAULT CERT UTIL *: vaultgetcert was unable to authenticate with Vault, but no error occured "
             ":(.")
        sys.exit(1)

    alt_names = args.subject_alt_names or ""
    if args.git_include_commit_san:
        try:
            output = subprocess.check_output([args.git_binary, "rev-parse", "HEAD"],
                                             stderr=subprocess.STDOUT, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            _out("* ERR VAULT CERT UTIL *: Error %s. trying to get the Git commit hash (git rev-parse HEAD) failed "
                 "with\n%s" % (e.returncode, e.output))
            sys.exit(e.returncode)

        output = output.strip()
        if len(output) != 40:
            _out("* ERR VAULT CERT UTIL *: Git returned a commit-hash of length %s (%s) instead of 40." %
                 (len(output), output))
            sys.exit(1)

        if alt_names == "":
            alt_names = "%s.git" % output
        else:
            alt_names = "%s.git,%s" % (output, alt_names)

    try:
        res = vcl.write(args.vault_pki, common_name=args.common_name, alt_names=alt_names,
                        exclude_cn_from_sans=not args.include_cn_in_sans)
    except RequestException as e:
        _out("* ERR VAULT WRAPPER *: Unable to read Vault path %s. (%s)" % (args.cert_key, str(e)))
        sys.exit(1)

    if "data" not in res or "certificate" not in res["data"] or "private_key" not in res["data"]:
        _out("* ERR VAULT CERT UTIL *: Vault returned a value without the necessary fields "
             "(data->certificate,private_key). Returned dict was:\n%s" %
             str(res))

    if not os.path.exists(os.path.dirname(args.certfile)):
        os.makedirs(os.path.dirname(args.certfile), mode=_get_masked_mode(args.mode_certs_dir), exist_ok=True)

    if not os.path.exists(os.path.dirname(args.keyfile)):
        os.makedirs(os.path.dirname(args.keyfile), mode=_get_masked_mode(args.mode_key_dir), exist_ok=True)

    with open(args.certfile, "wt", encoding="ascii") as certfile, \
            open(args.keyfile, "wt", encoding="ascii") as keyfile:
        os.chmod(args.certfile, _get_masked_mode(args.mode_certbundle_files))
        os.chmod(args.keyfile, _get_masked_mode(args.mode_key_file))

        certfile.write(res["data"]["certificate"].strip())
        certfile.write("\n")
        keyfile.write(res["data"]["private_key"].strip())
        keyfile.write("\n")

        if args.certchain:
            with open(args.certchain, "wt", encoding="ascii") as certchain:
                certchain.write(res["data"]["issuing_ca"].strip())
                certchain.write("\n")

    _out("* INF VAULT CERT UTIL *: the issued certificate and key have been stored in %s and %s" %
          (args.certfile, args.keyfile))
    if args.certchain:
        _out("* INF VAULT CERT UTIL *: the certificate chain has been stored in %s" % args.certchain)

    vault_pubkey = crypto.load_certificate(
        crypto.FILETYPE_PEM,
        res["data"]["issuing_ca"]
    ).get_pubkey().to_cryptography_key().public_numbers()

    vault_subject = crypto.load_certificate(
        crypto.FILETYPE_PEM,
        res["data"]["issuing_ca"]
    ).get_subject().get_components()

    if args.bundlepath and not os.path.exists(args.bundlepath):
        os.makedirs(args.bundlepath, mode=args.mode_certs_dir, exist_ok=True)

    for bundlename in xsign_bundles.keys():
        if xsign_bundles[bundlename] is None:
            x509str = res["data"]["issuing_ca"]
        else:
            with open(xsign_bundles[bundlename], mode="rt", encoding="ascii") as xcacert:
                x509str = xcacert.read()

        # the cross-signing certificate must sign the same keypair as the issueing_ca returned by Vault.
        # Let's check...
        xsign_pubkey = crypto.load_certificate(crypto.FILETYPE_PEM, x509str).get_pubkey() \
            .to_cryptography_key().public_numbers()

        if vault_pubkey != xsign_pubkey:
            xsign_subject = crypto.load_certificate(crypto.FILETYPE_PEM, x509str).get_subject().get_components()
            _out("* ERR VAULT CERT UTIL *: Cross-signing certificate %s has a different public key as the CA returned "
                 "by Vault. This certificate is invalid for the bundle.\n"
                 "***Xsign subject***\n%s\n***Vault subject***\n%s" %
                 (bundlename,
                  ", ".join(["%s=%s" % (k.decode("utf-8"), v.decode("utf-8")) for k, v in xsign_subject]),
                  ", ".join(["%s=%s" % (k.decode("utf-8"), v.decode("utf-8")) for k, v in vault_subject])))
            sys.exit(1)

        fn = bundlename
        if args.bundlepath and not os.path.isabs(bundlename):
            fn = os.path.join(args.bundlepath, bundlename)

        with open(fn, "wt", encoding="ascii") as bundle:
            _out("* INF VAULT CERT UTIL *: Creating bundle %s" % fn)
            bundle.write(res["data"]["certificate"].strip())
            bundle.write("\n")
            bundle.write(x509str.strip())
            bundle.write("\n")

    if args.output and args.envdir_mode:
        if not os.path.exists(args.output):
            os.makedirs(args.output, mode=_get_masked_mode(0o755), exist_ok=True)
        _result = functools.partial(_result_envdir, args.output)
        _out("writing envdir to %s" % args.output)
    elif args.output:
        if not os.path.exists(os.path.dirname(args.output)):
            os.makedirs(os.path.dirname(args.output), mode=_get_masked_mode(0o755), exist_ok=True)
        out_target = cast(TextIO, open(args.output, mode="wt", encoding="utf-8"))
        _out("writing output to %s" % args.output)

    for bundleref in bundle_vars.keys():
        # _result goes to stdout or --output
        fn = bundleref
        if args.bundlepath and not os.path.isabs(bundleref):
            fn = os.path.join(args.bundlepath, bundleref)
        _result(bundle_vars[bundleref]["envvar"],
                fn.replace(os.path.dirname(fn), bundle_vars[bundleref]["altpath"])
                if bundle_vars[bundleref]["altpath"] else fn)

    for keyvar in args.key_envvars:
        if ":" in keyvar:
            envvar, altpath = keyvar.split(":", 1)
        else:
            envvar, altpath = keyvar, None

        _result(envvar, args.keyfile.replace(os.path.dirname(args.keyfile), altpath) if altpath else args.keyfile)

    if args.output:
        out_target.close()

    _out("*** Done.")


if __name__ == "__main__":
    main()
