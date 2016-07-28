# -* encoding: utf-8 *-
import os
import tarfile
from typing import Sequence

import configargparse


def create_targzip(outfile: str, paths: Sequence[str], args: configargparse.Namespace,
                   make_paths_relative: bool=False) -> None:
    """
    creates a .tar.gz of everything below basepath, making sure all
    stored paths are relative
    """
    if os.path.exists(outfile):
        os.remove(outfile)

    with open(outfile, 'w') as f:
        # we're using stream mode here as otherwise tarfile seems
        # to add spurious information about f's path to the gzip
        # wrapper... this can be seen inside 7-zip :(
        with tarfile.open(fileobj=f, mode='w|gz') as tf:
            for path in paths:
                if os.path.exists(path) and os.path.isdir(path):
                    for root, dir, files in os.walk(path):
                        for filename in files:
                            filepath = os.path.join(root, filename)
                            arcpath = root
                            if make_paths_relative:
                                arcpath = root[len(path):]
                            arcname = os.path.join(arcpath, filename)
                            if args.verbose:
                                print('adding %s as %s' % (filepath, arcname,))
                            tf.add(filepath, arcname, recursive=False)

                elif os.path.exists(path) and os.path.isfile(path):
                    tf.add(path, path, recursive=False)
