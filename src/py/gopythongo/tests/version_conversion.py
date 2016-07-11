# -* encoding: utf-8 *-
import argparse
from unittest.case import TestCase
from collections import namedtuple
from typing import List, Any, cast

from gopythongo.utils.debversion import DebianVersion
from gopythongo.versioners.parsers import VersionContainer
from gopythongo.versioners.parsers.debianparser import DebianVersionParser
from gopythongo.versioners.parsers.pep440parser import PEP440VersionParser, PEP440Adapter
from gopythongo.versioners.parsers.semverparser import SemVerVersionParser, SemVerAdapter


_Args = namedtuple("_Args", ["semver_partial", "semver_coerce"])
args = cast(argparse.Namespace, _Args(semver_partial=False, semver_coerce=False))


class VersionConversionTests(TestCase):
    def _testeachless(self, *test: Any) -> None:
        ix = 1
        b = test[0]
        while ix < len(test):
            a = b
            b = test[ix]
            self.assertLess(a, b)
            ix += 1

    def test_semver_debian(self):
        dvp = DebianVersionParser()
        svp = SemVerVersionParser()

        self._testeachless(dvp.convert_from(svp.parse("1.2.3-1", args)).version,
                           dvp.convert_from(svp.parse("1.2.3-1.1", args)).version,
                           dvp.convert_from(svp.parse("1.2.3", args)).version)

        self._testeachless(svp.parse("1.2.3-1", args).version,
                           svp.parse("1.2.3-1.1", args).version,
                           svp.parse("1.2.3", args).version)

    def test_pep440_debian(self):
        dvp = DebianVersionParser()
        pvp = PEP440VersionParser()
        self._testeachless(
            dvp.convert_from(pvp.parse("1.2.3.a1", args)).version,
            dvp.convert_from(pvp.parse("1.2.3-a2", args)).version,
            dvp.convert_from(pvp.parse("1.2.3-rc1", args)).version,
            dvp.convert_from(pvp.parse("1.2.3", args)).version,
            dvp.convert_from(pvp.parse("1.2.3-1", args)).version,      # ==post1
            dvp.convert_from(pvp.parse("1.2.3-post2", args)).version,  # ==post2
            dvp.convert_from(pvp.parse("1.2.3-rev3", args)).version    # ==post3
        )
