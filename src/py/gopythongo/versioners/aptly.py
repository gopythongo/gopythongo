# -* encoding: utf-8 *-

import sys

import gopythongo.shared.aptly_args as _aptly_args

from gopythongo.versioners import BaseVersioner
from gopythongo.utils.debversion import DebianVersion, InvalidDebianVersionString
from gopythongo.utils import highlight, print_error, run_process


class AptlyVersioner(BaseVersioner):
    def __init__(self, *args, **kwargs):
        super(AptlyVersioner, self).__init__(*args, **kwargs)

    @property
    def versioner_name(self):
        return u"aptly"

    @property
    def can_read(self):
        return True

    @property
    def can_create(self):
        return True

    def can_execute_action(self, action):
        if action in ["increment-epoch-if-exists", "increment-revision-if-exists"]:
            return True
        return False

    def print_help(self):
        pass

    def add_args(self, parser):
        _aptly_args.add_shared_args(parser)

        gr_aptly = parser.add_argument_group("Aptly Versioner")
        gr_aptly.add_argument("--fallback-version", dest="aptly_fallback_version", default=None,
                              help="If the APT repository does not yet contain a package with the name specified by "
                                   "--package-name, the Aptly versioner can return a fallback value. This is useful "
                                   "for fresh repositories.")
        gr_aptly.add_argument("--aptly-versioner-opts", dest="aptly_versioner_opts", default=[],
                              help="Specify additional command-line parameters which will be appened to every "
                                   "invocation of aptly by the Aptly Versioner.")

    def validate_args(self, args):
        _aptly_args.validate_shared_args(args)

        if args.aptly_fallback_version:
            try:
                DebianVersion.fromstring(args.aptly_fallback_version)
            except InvalidDebianVersionString as e:
                print_error("The fallback version string you specified via %s is not a valid Debian version string. "
                            "(%s)" % (highlight("--fallback-version"), str(e)))
                sys.exit(1)

        if not args.package_name:
            print_error("To use the Aptly Versioner, you must specify --package-name.")

    def read(self, args):
        cmd = _aptly_args.get_aptly_cmdline(args)

        if args.aptly_versioner_opts:
            cmd += args.aptly_versioner_opts

        cmd += ["package", "search", "-format=\"{{.Version}}\"", args.package_name]

        output = run_process(cmd)



    def create(self, args):
        pass

    @property
    def operates_on(self):
        return [u"debian"]

    def execute_action(self, version, action):
        pass


versioner_class = AptlyVersioner
