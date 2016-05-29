# -* encoding: utf-8 *-

import collections
import subprocess
import sys
import os

import colorama
from colorama import Fore, Style

from . import buildcontext, debversion, plugins, template


success_color = Fore.LIGHTGREEN_EX
debug_hl = Fore.LIGHTMAGENTA_EX
debug_color = Fore.MAGENTA
info_hl = Fore.LIGHTCYAN_EX
info_color = Fore.LIGHTBLUE_EX
warning_hl = Fore.LIGHTYELLOW_EX
warning_color = Fore.YELLOW
error_hl = Fore.LIGHTRED_EX
error_color = Fore.RED
highlight_color = Fore.LIGHTWHITE_EX
color_reset = Fore.RESET

debug_donotexecute = False
prepend_exec = None
enable_debug_output = False

if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 3):
    from backports.shutil_get_terminal_size import get_terminal_size
    _cwidth, _cheight = get_terminal_size()
else:
    import shutil
    _cwidth, _cheight = shutil.get_terminal_size()


def init_color(no_color):
    global success_color, info_hl, info_color, warning_hl, warning_color, error_hl, error_color, highlight_color, \
        color_reset

    if no_color:
        success_color = info_hl = info_color = warning_hl = warning_color = error_hl = error_color = highlight_color =\
               color_reset = ""
    else:
        colorama.init()


def create_script_path(virtualenv_path, script_name):
    """
    creates a platform aware path to an executable inside a virtualenv
    """
    if sys.platform == "win32":
        f = os.path.join(virtualenv_path, "Scripts\\", script_name)
        if os.path.exists(f):
            return f
        else:
            return os.path.join(virtualenv_path, "Scripts\\", "%s.exe" % script_name)
    else:
        return os.path.join(virtualenv_path, "bin/", script_name)


def flatten(x):
    result = []
    for el in x:
        if isinstance(el, collections.Iterable) and not isinstance(el, str):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def run_process(*args, raise_nonzero_exitcode=False):
    if prepend_exec:
        args = prepend_exec + list(args)

    print_debug("Running %s" % str(args))
    if not debug_donotexecute:

        exitcode = 0
        try:
            output = subprocess.call(args, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            if raise_nonzero_exitcode:
                raise
            exitcode = e.returncode

        if exitcode != 0:
            print_error("%s exited with non-zero exit code %s" % (str(args), exitcode))
            sys.exit(exitcode)

        return output.strip().decode("utf-8")


def print_error(message):
    err = "%s%s%s%s%s" % (error_hl, "***", error_color, " ERROR: ", color_reset)
    print("%s%s" % (err, message))


def print_warning(message):
    warn = "%s%s%s%s%s" % (warning_hl, "***", warning_color, " WARNING: ", color_reset)
    print("%s%s" % (warn, message))


def print_info(message):
    info = "%s%s%s%s%s" % (info_hl, "*", info_color, " Info: ", color_reset)
    print("%s%s" % (info, message))


def print_debug(message):
    if enable_debug_output:
        debug = "%s%s%s%s%s" % (debug_hl, "*", debug_color, " Debug: ", color_reset)
        print("%s%s" % (debug, message))


def success(message):
    print("%s%s%s" % (success_color, message, color_reset))


def highlight(message):
    return "%s%s%s" % (highlight_color, message, color_reset)


class GoPythonGoEnableSuper(object):
    def __init__(self, *args, **kwargs):
        pass


class CommandLinePlugin(GoPythonGoEnableSuper):
    def __init__(self, *args, **kwargs):
        super(CommandLinePlugin, self).__init__(*args, **kwargs)

    def add_args(self, parser):
        """
        Add command-line arguments to configure this plugin inside GoPythonGo. Do NOT add *required* arguments
        to the command-line parser.

        :param parser: An ArgumentParser instance that you can call ``add_argument_group`` etc. on
        :type parser: argparse.ArgumentParser
        """
        pass

    def validate_args(self, args):
        """
        Validate the arguments added by ``add_args``. Feel free to call ``sys.exit(1)`` from here if any argument
        is invalid. Please use ``gopythongo.utils.print_error`` to output a meaningful error message to the user before
        exiting.

        :param args: The parsed command-line arguments as provided by argparse
        """
        pass
