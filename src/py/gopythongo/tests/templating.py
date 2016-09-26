# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittest.case import TestCase

from gopythongo.utils import template


class TemplateStringParsingTest(TestCase):
    def test_template_parsing(self) -> None:
        teststr = '--test1=template:blah -t template:"xyz" -f "template:contained"'
        pswt = template.parse_template_prefixes(teststr)
        self.assertEqual(pswt.original, teststr)
        self.assertEqual(pswt.format_str, "--test1={0} -t {1} -f \"{2}\"")
        self.assertListEqual(pswt.templates, ["blah", '"xyz"', "contained"])
