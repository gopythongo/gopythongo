# -* encoding: utf-8 *-
import collections
import subprocess
import configargparse
import sys
import os

from typing import List, Iterable, Union, Any, cast, IO

import colorama
from colorama import Fore


success_color = Fore.LIGHTGREEN_EX  # type: str
debug_hl = Fore.LIGHTMAGENTA_EX  # type: str
debug_color = Fore.MAGENTA  # type: str
info_hl = Fore.LIGHTCYAN_EX  # type: str
info_color = Fore.LIGHTBLUE_EX  # type: str
warning_hl = Fore.LIGHTYELLOW_EX  # type: str
warning_color = Fore.YELLOW  # type: str
error_hl = Fore.LIGHTRED_EX  # type: str
error_color = Fore.RED  # type: str
highlight_color = Fore.LIGHTWHITE_EX  # type: str
color_reset = Fore.RESET  # type: str

debug_donotexecute = False  # type: bool
prepend_exec = None  # type: List[str]
enable_debug_output = False  # type: bool

if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 3):
    from backports.shutil_get_terminal_size import get_terminal_size
    _cwidth, _cheight = get_terminal_size()
else:
    import shutil
    _cwidth, _cheight = shutil.get_terminal_size()  # type: ignore


def init_color(no_color: bool) -> None:
    global success_color, info_hl, info_color, warning_hl, warning_color, error_hl, error_color, highlight_color, \
        color_reset

    if no_color:
        success_color = info_hl = info_color = warning_hl = warning_color = error_hl = error_color = highlight_color =\
               color_reset = ""
    else:
        colorama.init()


def create_script_path(virtualenv_path: str, script_name: str) -> str:
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


def flatten(x: Union[Iterable[str], str]) -> List[str]:
    result = []  # type: List[str]
    for el in x:
        if isinstance(el, collections.Iterable) and not isinstance(el, str):
            result.extend(flatten(el))
        else:
            # we cast here because mypy otherwise assumes el is Iterable[Any]
            # which it can't be... el could be Any but NOT Iterable
            result.append(cast(str, el))
    return result


class ProcessOutput(object):
    def __init__(self, output: str, exitcode: int) -> None:
        self.output = output
        self.exitcode = exitcode


def run_process(*args: str, allow_nonzero_exitcode: bool=False, raise_nonzero_exitcode: bool=False,
                interactive: bool=False, send_to_stdin: bytes=None) -> ProcessOutput:
    if prepend_exec:
        actual_args = prepend_exec + list(args)  # type: List[str]
    else:
        actual_args = list(args)

    print_debug("Running %s" % str(actual_args))
    if debug_donotexecute:
        return ProcessOutput("", 0)
    else:
        exitcode = 0

        if interactive:
            try:
                subprocess.call(actual_args)
            except subprocess.CalledProcessError as e:
                raise
            return ProcessOutput("", 0)
        else:
            try:
                if send_to_stdin:
                    output = subprocess.check_output(actual_args, stderr=subprocess.STDOUT,
                                                     input=send_to_stdin).decode("utf-8")
                else:
                    # it seems that mypy does not realize that universal_newlines guarantees a str return
                    output = cast(str, subprocess.check_output(actual_args,
                                  stderr=subprocess.STDOUT, universal_newlines=True))
            except subprocess.CalledProcessError as e:
                if raise_nonzero_exitcode:
                    raise
                exitcode = e.returncode
                if send_to_stdin:
                    output = e.output.decode("utf-8")
                else:
                    # because universal_newlines = True this will be str, but mypy doesn't know
                    output = cast(str, e.output)

            if exitcode != 0 and not allow_nonzero_exitcode:
                raise ErrorMessage("%s exited with non-zero exit code %s. Output was:\n%s" %
                                   (str(args), exitcode, output), exitcode=exitcode)

            if enable_debug_output:
                print(highlight("******** Subprocess output follows ********"))
                print(output)

            return ProcessOutput(output.strip(), exitcode)


def print_error(message: str) -> None:
    err = "%s%s%s%s%s" % (error_hl, "***", error_color, " ERROR: ", color_reset)
    print("%s%s" % (err, message))


def print_warning(message: str) -> None:
    warn = "%s%s%s%s%s" % (warning_hl, "***", warning_color, " WARNING: ", color_reset)
    print("%s%s" % (warn, message))


def print_info(message: str) -> None:
    info = "%s%s%s%s%s" % (info_hl, "*", info_color, " Info: ", color_reset)
    print("%s%s" % (info, message))


def print_debug(message: str) -> None:
    if enable_debug_output:
        debug = "%s%s%s%s%s" % (debug_hl, "*", debug_color, " Debug: ", color_reset)
        print("%s%s" % (debug, message))


def success(message: str) -> None:
    print("%s%s%s" % (success_color, message, color_reset))


def highlight(message: str) -> str:
    return "%s%s%s" % (highlight_color, message, color_reset)


class GoPythonGoEnableSuper(object):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass


class CommandLinePlugin(GoPythonGoEnableSuper):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        """
        Add command-line arguments to configure this plugin inside GoPythonGo. Do NOT add *required* arguments
        to the command-line parser.

        :param parser: An ArgumentParser instance that you can call ``add_argument_group`` etc. on
        :type parser: configargparse.ArgumentParser
        """
        pass

    def validate_args(self, args: configargparse.Namespace) -> None:
        """
        Validate the arguments added by ``add_args``. Feel free to raise ``ErrorMessage`` from here if any argument
        is invalid.

        :param args: The parsed command-line arguments as provided by configargparse
        """
        pass


class ErrorMessage(Exception):
    def __init__(self, ansi_msg: str, exitcode: int=1) -> None:
        super().__init__(ansi_msg)
        self.ansi_msg = ansi_msg
        self.exitcode = exitcode

    def __str__(self) -> str:
        return self.ansi_msg
