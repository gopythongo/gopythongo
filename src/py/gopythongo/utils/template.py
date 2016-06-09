# -* encoding: utf-8 *-
import os
from typing import Dict, Any

import tempfile
import jinja2


def process_to_tempfile(filepath: str, context: Dict[str, Any]) -> str:
    """
    renders the template in ``filepath`` using ``context`` through Jinja2. The result
    is saved into a temporary file, which will be garbage collected automatically when the
    program exits.

    :return: the full path of the temporary file containing the result
    """
    outfd, ofname = tempfile.mkstemp()
    outf = open(outfd, mode="w")
    with open(filepath) as inf:
        tplstr = inf.read()
    tpl = jinja2.Template(tplstr)
    outf.write(tpl.render(context))
    outf.close()

    import gopythongo.main
    gopythongo.main.tempfiles.append(ofname)
    return ofname
