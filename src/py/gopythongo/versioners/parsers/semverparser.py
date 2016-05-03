# -* encoding: utf-8 *-

import six

from semantic_version import Version as SemVerBase
from gopythongo.utils import highlight, print_error
from gopythongo.versioners.parsers.base import VersionContainer, UnconvertableVersion, BaseVersionParser


class SemVerVersion(SemVerBase):
    def __init__(self, *args):
        super(SemVerVersion, self).__init__(*args)

    def tostring(self):
        return six.u(self)


class SemVerVersionParser(BaseVersionParser):
    def __init__(self, *args, **kwargs):
        super(SemVerVersionParser, self).__init__(*args, **kwargs)

    @property
    def versionparser_name(self):
        return u"semver"

    def add_args(self, parser):
        gr_semver = parser.add_argument_group("SemVer Versioner")
        gr_semver.add_argument("--semver-allow-partial", dest="semver_partial", action="store_true", default=False,
                               help="Allow the parsing of incomplete version strings, which still partially comply "
                                    "with SemVer (e.g. '2.0')")
        gr_semver.add_argument("--semver-coerce", dest="semver_coerce", action="store_true", default=False,
                               help="Try really hard to make the input version into something resembling SemVer. Use "
                                    "this with caution.")

    def parse(self, version_str, args):
        try:
            sv = SemVerVersion.parse(version_str, partial=args.semver_partial, coerce=args.semver_coerce)
        except ValueError as e:
            print_error("%s is not a valid SemVer version string (%s)" % (highlight(version_str), str(e)))

        return VersionContainer(sv, self.versionparser_name)

    def print_help(self):
        pass


versionparser_class = SemVerVersionParser
