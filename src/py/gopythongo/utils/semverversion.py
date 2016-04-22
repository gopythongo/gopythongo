# -* encoding: utf-8 *-

#
# SemVer specifies the following format
#   major.minor.patchlevel-prerelease.identifiers+build.metadata


class SemVerVersion(object):
    def __init__(self, major, minor, patchlevel, revision=None, buildmeta=None):
        self.major = major
        self.minor = minor
        self.patchlevel = patchlevel
        self.revision = revision
        self.buildmeta = buildmeta

    def validate(self):
        """
        :raises InvalidSemVerVersionString: if this SemVerVersion object is invalid in the eyes of semver.org
        """

    @staticmethod
    def fromstring(version_str):
        pass
