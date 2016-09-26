# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import tempfile

from typing import Dict, Any, List

import jinja2

from gopythongo.utils import GoPythonGoEnableSuper, ErrorMessage


def process_to_tempfile(filepath: str, context: Dict[str, Any]) -> str:
    """
    renders the template in ``filepath`` using ``context`` through Jinja2. The result
    is saved into a temporary file, which will be garbage collected automatically when the
    program exits.

    :return: the full path of the temporary file containing the result
    """
    outfd, ofname = tempfile.mkstemp()
    with open(outfd, mode="w") as outf:
        with open(filepath) as inf:
            tplstr = inf.read()
        tpl = jinja2.Template(tplstr)
        outf.write(tpl.render(context))

    import gopythongo.main
    gopythongo.main.tempfiles.append(ofname)
    return ofname


def process_in_memory(filepath: str, context: Dict[str, Any]) -> str:
    """
    renders the template in ``filepath`` using ``context`` through Jinja2. The result
    is saved into a ``str``.

    :return: the processed result
    """
    with open(filepath) as inf:
        tplstr = inf.read()
    tpl = jinja2.Template(tplstr)
    return tpl.render(context)


class ProcessedStringWithTemplates(GoPythonGoEnableSuper):
    def __init__(self, original: str, format_str: str, templates: List[str]=None, *args: Any,
                 **kwargs: Any) -> None:
        super().__init__(original, format_str, templates, *args, **kwargs)
        self.original = original  # type: str
        self.format_str = format_str  # type: str
        self.templates = templates or []  # type: List[str]


def parse_template_prefixes(input: str) -> ProcessedStringWithTemplates:
    """
    Transforms ``--test1=template:blah -x template:"xyz"`` into ``--test1={0} -x {1}`` and returns a
    ``ProcessedStringWithTemplates`` instance (henceforth ``pswt``) that contains ``input``, the resulting format
    string and a list of all templates to be processed. The number of format placeholders in the ``pswt.format_str``
    attribute is ``len(pswt.templates)``.

    :param input: the string which might contain a template: prefix
    :return: an instance of ``ProcessedStringWithTemplates`` or None if there are no template strings
    """
    stripped = input.strip()

    if "template:" not in input:
        return None

    result = ""
    remaining_input = input
    templates = []
    for ix in range(0, input.count("template:")):
        # slice remaining input string at "template:"
        sub = remaining_input[remaining_input.index("template:") + len("template:"):]
        result = "%s%s" % (result, remaining_input[0:remaining_input.index("template:")])
        # basic quoting
        if sub.startswith('"'):
            if '"' not in sub[1:]:  # missing closing quote
                raise ErrorMessage("Failed to parse %s. It seems to be missing a closing quote." % sub)
            filename = sub[0:sub[1:].index('"') + 2]  # +2 because sub[1:] is 1 shorter and we want to include the quote
        else:
            if " " in sub:
                filename = sub[0:sub.index(" ")]
            else:
                # we need to handle the special case that filename can end in '"' if input contained
                # '--example "template:fn"'
                if sub.endswith('"'):
                    filename = sub[0:-1]
                else:
                    filename = sub

        remaining_input = remaining_input[remaining_input.index("template:") + len("template:") + len(filename):]
        result = "%s{%s}" % (result, ix)
        templates.append(filename)

    result = "%s%s" % (result, remaining_input)  # append the remainder of the input string
    return ProcessedStringWithTemplates(input, result, templates)
