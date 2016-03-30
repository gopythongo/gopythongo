# -* encoding: utf-8 *-

import subprocess
import time
import sys
import os


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


def run_process(*args):
    print("Running %s" % str(args))
    process = subprocess.Popen(args, stdout=sys.stdout, stderr=sys.stderr)
    while process.poll() is None:
        time.sleep(1)

    if process.returncode != 0:
        print("%s exited with return code %s" % (str(args), process.returncode))
        sys.exit(process.returncode)


class BuildContext(object):
    pass
