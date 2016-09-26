# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import tarfile

from io import BytesIO
from typing import Sequence, Union, cast, Tuple


def create_targzip(*, filename: str=None, paths: Sequence[Tuple[str, str]], verbose: bool=False,
                   make_paths_relative: bool=False) -> Union[BytesIO, None]:
    """
    Creates a .tar.gz of everything below paths, making sure all
    stored paths are relative if make_paths_relative is `True`.

    :param filename: the name of a file to write to, or `None`. If filename is `None` `create_targzip` returns
                     a `BinaryIO` in-memory file (be careful with the memory allocation here).
    :param paths: a list of folders and files to add to the output .tar.gz. Each list item is a ``tuple`` of the form
                  ``(path/filename, mapped path/mapped filename)`` allowing you to rename folders or files *inside*
                  the .tar.gz ny using a tuple. For example: The Docker Builder uses this to pack '/tmp/xyz1234' as
                  '/Dockerfile' into the Docker context .tar.gz.
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
    for pspec in paths:
        path = pspec[0]
        altpath = pspec[1] if pspec[1] else None

        if os.path.exists(path) and os.path.isdir(path):
            for root, dir, files in os.walk(path):
                for fn in files:
                    filepath = os.path.join(root, fn)
                    arcpath = root
                    if altpath:
                        arcpath = altpath
                    elif make_paths_relative:
                        arcpath = root[len(path):]
                    arcname = os.path.join(arcpath, fn)
                    if verbose:
                        print('adding %s as %s' % (filepath, arcname,))
                    tf.add(filepath, arcname, recursive=False)

        elif os.path.exists(path) and os.path.isfile(path):
            if verbose:
                print('adding %s as %s' % (path, altpath if altpath else path))
            tf.add(path, altpath if altpath else path, recursive=False)

    if filename:
        tf.close()
        f.close()
    else:
        tf.close()
        return cast(BytesIO, f)
