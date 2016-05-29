# -* encoding: utf-8 *-
import sys

from semantic_version import Version as SemVerBase
from gopythongo.utils import highlight, print_error
from gopythongo.versioners.parsers import VersionContainer, BaseVersionParser


class SemVerVersion(SemVerBase):
    def __init__(self, *args):
        super(SemVerVersion, self).__init__(*args)

    def tostring(self):
        return str(self)


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
            sys.exit(1)

        return VersionContainer(sv, self.versionparser_name)

    def print_help(self):
        print("%s\n"
              "=====================\n"
              "\n"
              "The %s parser parses SemVer version strings as defined by\n"
              "http://semver.org/. It does not require any additional command-line parameters,\n"
              "but it can parse *partial* SemVer strings that don't fully conform to the SemVer\n"
              "specification or even try and transform arbitrary strings. You can enable those\n"
              "features with the following command-line flags:\n"
              "\n"
              "    --semver-allow-partial    Enables partial string parsing, like '1.0'\n"
              "    --semver-coerce           Tries to convert anything you throw at it, like\n"
              "                              '1.0.whatever' to varied levels of success.\n" %
              (highlight("SemVer Version Parser"), highlight("semver")))


versionparser_class = SemVerVersionParser
