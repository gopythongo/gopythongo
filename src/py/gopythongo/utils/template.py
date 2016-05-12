# -* encoding: utf-8 *-

import tempfile
import jinja2


def process_to_tempfile(filepath, context):
    """
    renders the template in ``filepath`` using ``context`` through Jinja2. The result
    is saved into a temporary file, which will be garbage collected automatically when the
    program exits.

    :return: the full path of the temporary file containing the result
    """
    outf, ofname = tempfile.mkstemp()
    with open(filepath) as inf:
        tplstr = inf.read()
    tpl = jinja2.Template(tplstr)
    outf.write(tpl.render(context))
    outf.close()

    import gopythongo
    gopythongo.main.tempfiles.append(outf)
    return ofname
