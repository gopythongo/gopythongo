# -* encoding: utf-8 *-
import os
import sys
import hvac
import configargparse

from typing import List, Sequence, Iterable, Union, Any

from OpenSSL import crypto
from requests.exceptions import RequestException


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
                    "--help-verbose to learn more. vaultgetcert expects everything to be PEM encoded. "
                    "It cannot convert between different formats.",
        prog="gopythongo.vaultgetcert",
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
    parser.add_argument("--certfile-out", dest="certfile", required=True,
                        help="Path of the file where the generated certificate will be stored.")
    parser.add_argument("--keyfile-out", dest="keyfile", required=True,
                        help="Path of the file where the generated private key will be stored. Permissions for this "
                             "file will be set to 600.")
    parser.add_argument("--certchain-out", dest="certchain", default=None,
                        help="Save the issuer CA certificate, which is likely the intermediate CA that you need to "
                             "provide in the certificate chain.")
    parser.add_argument("--overwrite", dest="overwrite", default=False, action="store_true",
                        help="When set, this program will overwrite existing certificates and keys on disk.")
    parser.add_argument("--help-verbose", action=HelpAction,
                        help="Show additional information about how to set up Vault for using vaultgetcert.")

    gp_xsign = parser.add_argument_group("Handling cross-signing CAs")
    gp_xsign.add_argument("--xsign-cacert", dest="xsigners", default=[], action="append",
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
    gp_xsign.add_argument("--xsign-bundle-path", dest="bundlepath", default=None,
                          help="A folder where all of the generated files without absolute paths from specified "
                               "--xsign-cacert parameters will be stored. Existing bundles will be overwritten.")
    gp_xsign.add_argument("--output-bundle-envvar", dest="bundle_envvars", default=[], action="append",
                          help="Can be specified multiple times. The argument must be in the form "
                               "'envvar=bundlename[:altpath]' (altpath is optional). "
                               "For each envvar specified vaultgetcert will output 'envvar=bundlepath' to stdout. If "
                               "you specify 'altpath', 'altpath' will replace the FULL path in bundlepath. The "
                               "filename will stay the same. This output is meant to be used as configuration "
                               "environment variables for your program and can be shipped, for example, for usage in "
                               "/etc/default.")

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

    if args.wrap_program and (not os.path.exists(args.wrap_program) or not os.access(args.wrap_program, os.X_OK)):
        _out("* ERR VAULT CERT UTIL *: Wrapped executable %s doesn't exist or is not executable." % args.wrap_program)
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

    if os.path.exists(args.keyfile) and not args.overwrite:
        _out("* ERR VAULT CERT UTIL *: %s already exists and --overwrite is not specified" % args.keyfile)
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
        if not os.path.exists(args.bundlepath) or not os.access(args.bundlepath, os.W_OK):
            _out("* ERR VAULT CERT UTIL *: %s does not exist or is not writable" % args.bundlepath)

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


def main() -> None:
    _out("* INF VAULT CERT UTIL *: cwd is %s" % os.getcwd())
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
        _out("* ERR VAULT CERT UTIL *: Failure while authenticating to Vault. (%s)" % str(e))
        sys.exit(1)
    if not vcl.is_authenticated():
        _out("* ERR VAULT CERT UTIL *: vaultgetcert was unable to authenticate with Vault, but no error occured "
             ":(.")
        sys.exit(1)

    with open(args.certfile, "wt", encoding="ascii") as certfile, \
            open(args.keyfile, "wt", encoding="ascii") as keyfile:
        os.chmod(args.keyfile, 0o0600)
        try:
            res = vcl.write(args.cert_key)
        except RequestException as e:
            _out("* ERR VAULT WRAPPER *: Unable to read Vault path %s. (%s)" % (args.cert_key, str(e)))
            sys.exit(1)

        if "data" not in res or "certificate" not in res["data"] or "private_key" not in res["data"]:
            _out("* ERR VAULT CERT UTIL *: Vault returned a value without the necessary fields "
                 "(data->certificate,private_key). Returned dict was:\n%s" %
                 str(res))
        certfile.write(res["data"]["certificate"])
        keyfile.write(res["data"]["keyfile"])

        if args.certchain:
            with open(args.certchain, "wt", encoding="ascii") as certchain:
                certchain.write(res["data"]["issuing_ca"])

    _out("* INF VAULT CERT UTIL *: the issued certificate and key have been stored in %s and %s" %
          (args.certfile, args.keyfile))
    if args.certchain:
        _out("* INF VAULT CERT UTIL *: the certificate chain has been stored in %s" % args.certchain)

    vault_pubkey = crypto.load_certificate("pem", res["data"]["issuing_ca"]).get_pubkey() \
                        .to_cryptography_key().public_numbers()
    vault_subject = crypto.load_certificate("pem", res["data"]["issuing_ca"]).get_subject().get_components()

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
                 "by Vault. This certificate is invalid for the bundle.\nXsign subject: %s\nVault subject: %s" %
                 (bundlename,
                  ", ".join(["%s=%s" % (k.decode("utf-8"), v.decode("utf-8")) for k, v in xsign_subject]),
                  ", ".join(["%s=%s" % (k.decode("utf-8"), v.decode("utf-8")) for k, v in vault_subject])))
            sys.exit(1)

        if os.path.isabs(bundlename):
            fn = bundlename
        else:
            fn = os.path.join(args.bundlepath, bundlename)

        with open(fn, "wt", encoding="ascii") as bundle:
            _out("* INF VAULT CERT UTIL *: Creating bundle %s" % fn)
            bundle.write(res["data"]["certificate"])
            bundle.write(x509str)

    for bundleref in bundle_vars.keys():
        # print goes to stdout
        if os.path.isabs(bundleref):
            fn = bundleref
        else:
            fn = os.path.join(args.bundlepath, bundleref)
        print("%s=\"%s\"" %
              (bundle_vars[bundleref]["envvar"],
               fn.replace(os.path.dirname(fn), bundle_vars[bundleref]["altpath"])
                  if bundle_vars[bundleref]["altpath"] else fn))

    _out("*** Done.")


if __name__ == "__main__":
    main()
