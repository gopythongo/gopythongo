# -* encoding: utf-8 *-
from unittest.case import TestCase
from gopythongo.utils.debversion import debian_substr_compare, split_version_parts, DebianVersion, \
                                        InvalidDebianVersionString


class DebianVersionTests(TestCase):
    def test_debian_substr_compare(self) -> None:
        self.assertEqual(debian_substr_compare("", "a"), -1)
        self.assertEqual(debian_substr_compare("09", "10"), -1)
        self.assertEqual(debian_substr_compare("~~", "~"), -1)
        self.assertEqual(debian_substr_compare("~~", "~~a"), -1)
        self.assertEqual(debian_substr_compare("~~", "~~"), 0)
        self.assertEqual(debian_substr_compare("~", ""), -1)
        self.assertEqual(debian_substr_compare("30", "30"), 0)

    def test_debian_version_compare(self) -> None:
        self.assertTrue(DebianVersion.fromstring("2:1.0") < DebianVersion.fromstring("3:1.0"))
        self.assertTrue(DebianVersion.fromstring("2:1.0~1") < DebianVersion.fromstring("3:1.0"))
        self.assertTrue(DebianVersion.fromstring("2:1.0~bpo1") < DebianVersion.fromstring("2:1.0"))
        self.assertTrue(DebianVersion.fromstring("2:1.0dev") > DebianVersion.fromstring("2:1.0"))
        self.assertTrue(DebianVersion.fromstring("1.0dev") > DebianVersion.fromstring("1.0"))
        self.assertTrue(DebianVersion.fromstring("1.0-1") > DebianVersion.fromstring("1.0"))
        self.assertTrue(DebianVersion.fromstring("1.0-2") > DebianVersion.fromstring("1.0-1"))
        self.assertTrue(DebianVersion.fromstring("1.0") == DebianVersion.fromstring("1.0"))
        self.assertTrue(DebianVersion.fromstring("0:1.0") == DebianVersion.fromstring("1.0"))

    def test_split_version_parts(self) -> None:
        self.assertListEqual(split_version_parts("a67bhgs89"), ["a", "67", "bhgs", "89"])
        self.assertListEqual(split_version_parts("33a67bhgs89"), ["33", "a", "67", "bhgs", "89"])
        self.assertListEqual(split_version_parts("~33a67bhgs89"), ["~", "33", "a", "67", "bhgs", "89"])
        self.assertListEqual(split_version_parts("33~a67bhgs89"), ["33", "~a", "67", "bhgs", "89"])
        self.assertListEqual(split_version_parts("1"), ["1"])
        self.assertListEqual(split_version_parts(""), [""])

    def test_serialization(self) -> None:
        v = DebianVersion.fromstring("2:1.0~bpo1")
        self.assertEqual(v, v.fromstring(v.tostring()))

    def test_sorting_compatibility_aptpkg(self) -> None:
        version_strings = ["~~a", "~", "~~", "a1", "1.0", "1.0-1", "1.0~bpo1", "1.0-1~bpo1"]
        # sorted using python-apt's apt_pkg.version_compare
        aptpkg_sorting = ['~~', '~~a', '~', '1.0~bpo1', '1.0', '1.0-1~bpo1', '1.0-1', 'a1']

        l = []
        for x in version_strings:
            l.append(DebianVersion.fromstring(x))

        l.sort()
        self.assertListEqual(aptpkg_sorting, [str(x) for x in l])

    def test_validation(self) -> None:
        self.assertRaises(InvalidDebianVersionString, DebianVersion.fromstring, "1.0:0")
        self.assertRaises(InvalidDebianVersionString, DebianVersion.fromstring, "ö:1.0")
        self.assertRaises(InvalidDebianVersionString, DebianVersion.fromstring, "1.Ö")
