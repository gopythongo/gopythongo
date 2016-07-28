# -* encoding: utf-8 *-
import os
import tarfile

from io import BytesIO
from typing import Sequence, Union, cast


def create_targzip(*, filename: str=None, paths: Sequence[str], verbose: bool=False,
                   make_paths_relative: bool=False) -> Union[BytesIO, None]:
    """
    Creates a .tar.gz of everything below paths, making sure all
    stored paths are relative if make_paths_relative is `True`.

    :param filename: the name of a file to write to, or `None`. If filename is `None` `create_targzip` returns
                     a `BinaryIO` in-memory file (be careful with the memory allocation here).
    :param paths: a list of folders and files to add to the output .tar.gz
    :param verbose: output each filename in paths as it is being processed
    :param make_paths_relative: ensure that the .tar.gz keeps all files relative to the path in paths. This is only
                                mildly useful if you pack up multiple paths
    """
    if filename:
        if os.path.exists(filename):
            os.remove(filename)
        f = open(filename, "wb")
    else:
        f = BytesIO()

    # we're using stream mode here as otherwise tarfile seems
    # to add spurious information about f's path to the gzip
    # wrapper... this can be seen inside 7-zip :(
    tf = tarfile.open(fileobj=f, mode='w|gz')
    for path in paths:
        if os.path.exists(path) and os.path.isdir(path):
            for root, dir, files in os.walk(path):
                for fn in files:
                    filepath = os.path.join(root, fn)
                    arcpath = root
                    if make_paths_relative:
                        arcpath = root[len(path):]
                    arcname = os.path.join(arcpath, fn)
                    if verbose:
                        print('adding %s as %s' % (filepath, arcname,))
                    tf.add(filepath, arcname, recursive=False)

        elif os.path.exists(path) and os.path.isfile(path):
            if verbose:
                print('adding %s as %s' % (path, path))
            tf.add(path, path, recursive=False)

    if filename:
        tf.close()
        f.close()
    else:
        tf.close()
        return cast(BytesIO, f)
