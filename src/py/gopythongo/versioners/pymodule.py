# -* encoding: utf-8 *-
import six
import sys

from importlib import import_module
from gopythongo.utils import print_error

__versioner_name__ = "pymodule"


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


def add_args(parser):
    pass


def validate_args(args):
    pass


def validate_param(param):
    try:
        import_string(param)
    except ImportError as e:
        print_error("Pymodule versioner can't import/read %s" % param)


def read(readspec):
    attr = import_string(readspec)
    if callable(attr):
        return attr()
    return attr


def print_help():
    print("The pymodule versioner reads version strings from Python modules which must be\n"
          "on PYTHONPATH. It accepts one parameter with is a dotted string identifying the\n"
          "fully qualified module name of a Python module and an attribute to read or\n"
          "function to call, which must be a unicode string (i.e. str on Py3k and unicode\n"
          "on Py2).\n"
          "\n"
          "Examples: --read-version='pymodule:gopythongo.__version__'\n"
          "          --read-version='pymodule:a.deeper.module.get_version\n")
