# -* encoding: utf-8 *-
import six
import sys

from gopythongo.versioners import BaseVersioner
from importlib import import_module
from gopythongo.utils import print_error, highlight


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.

    Blatantly copied from Django 1.9.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])


class PymoduleVersioner(BaseVersioner):
    def __init__(self, *args, **kwargs):
        super(PymoduleVersioner, self).__init__(*args, **kwargs)

    @property
    def versioner_name(self):
        return u"pymodule"

    def add_args(self, parser):
        gr_pymod = parser.add_argument_group("Pymodule Versioner")
        gr_pymod.add_argument("--pymodule-read", dest="pymodule_read", default=None,
                              help="A fully qualified dotted path to a str attribute in a Python module accessible on"
                                   "the current PYTHONPATH to be read to get the version string.")

    def validate_args(self, args):
        if args.pymodule_read:
            try:
                import_string(args.pymodule_read)
            except ImportError as e:
                print_error("Pymodule versioner can't import/read %s" % args.pymodule_read)
                sys.exit(1)
        else:
            print_error("%s requires %s" % (highlight("--versioner=pymodule"), highlight("--pymodule-read")))
            sys.exit(1)

    def read(self, readspec):
        attr = import_string(readspec)
        if callable(attr):
            return attr()
        return attr

    def print_help(self):
        print("The pymodule versioner reads version strings from Python modules which must be\n"
              "on PYTHONPATH. It accepts one parameter with is a dotted string identifying the\n"
              "fully qualified module name of a Python module and an attribute to read or\n"
              "function to call, which must be a unicode string (i.e. str on Py3k and unicode\n"
              "on Py2).\n"
              "\n"
              "Examples: --versioner='pymodule' --pymodule-read='gopythongo.version'\n"
              "          --versioner='pymodule' --pymodule-read='a.deeper.module.get_version'\n")


versioner_class = PymoduleVersioner
