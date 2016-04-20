# -* encoding: utf-8 *-

import collections
import subprocess
import shutil
import time
import six
import sys
import os

import colorama
from colorama import Fore, Style


success_color = Fore.LIGHTGREEN_EX
info_hl = Fore.LIGHTCYAN_EX
info_color = Fore.LIGHTBLUE_EX
warning_hl = Fore.LIGHTYELLOW_EX
warning_color = Fore.YELLOW
error_hl = Fore.LIGHTRED_EX
error_color = Fore.RED
highlight_color = Fore.LIGHTWHITE_EX
color_reset = Fore.RESET

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
        if isinstance(el, collections.Iterable) and not isinstance(el, six.string_types):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def run_process(*args):
    print_info("Running %s" % str(args))
    process = subprocess.Popen(args, stdout=sys.stdout, stderr=sys.stderr)
    while process.poll() is None:
        time.sleep(1)

    if process.returncode != 0:
        print_error("%s exited with non-zero exit code %s" % (str(args), process.returncode))
        sys.exit(process.returncode)


def print_error(message):
    err = "%s%s%s%s%s" % (error_hl, "***", error_color, " ERROR: ", color_reset)
    print("%s%s" % (err, message))


def print_warning(*args, **kwargs):
    print("%s%s%s%s%s" % (warning_hl, "***", warning_color, " WARNING: ", color_reset), end="")
    print(*args, **kwargs)


def print_info(*args, **kwargs):
    print("%s%s%s%s%s" % (info_hl, "*", info_color, " Info: ", color_reset), end="")
    print(*args, **kwargs)


def success(message):
    print("%s%s%s" % (success_color, message, color_reset))


def highlight(message):
    return "%s%s%s" % (highlight_color, message, color_reset)


class BuildContext(object):
    def __init__(self):
        self.packs = []
        self.read_version = None
        self.out_version = None
