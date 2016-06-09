# -* encoding: utf-8 *-
import argparse

import os
import sys
import shutil
import tarfile

from gopythongo.packers import BasePacker
from gopythongo.utils import print_info, print_error, highlight


class TarGzPacker(BasePacker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def packer_name(self) -> str:
        return u"targz"

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        pass

    def validate_args(self, args: argparse.Namespace) -> None:
        pass

    def _create_targzip(self, outfile: str, basepath: str, make_paths_relative: bool=False) -> None:
        """
        creates a .tar.gz of everything below basepath, making sure all
        stored paths are relative
        """
        global _args
        if os.path.exists(outfile):
            os.remove(outfile)

        f = open(outfile, 'w')
        # we're using stream mode here as otherwise tarfile seems
        # to add spurious information about f's path to the gzip
        # wrapper... this can be seen inside 7-zip :(
        tf = tarfile.open(fileobj=f, mode='w|gz')
        for root, dir, files in os.walk(basepath):
            for filename in files:
                filepath = os.path.join(root, filename)
                arcpath = root
                if make_paths_relative:
                    arcpath = root[len(basepath):]
                arcname = os.path.join(arcpath, filename)
                if _args.verbose:
                    print('adding %s as %s' % (filepath, arcname,))
                tf.add(filepath, arcname, recursive=False)
        tf.close()
        f.close()

    def _build_tar(self) -> None:
        global _args
        if _args.collect_static:
            _collect_static()

            if os.path.exists(_args.static_root):
                print_info("creating static tarball of %s in %s" % (highlight(_args.static_root),
                                                                    highlight(_args.static_outfile),))
                _create_targzip(_args.static_outfile, _args.static_root, _args.static_relative)
            else:
                print_error("%s should now exist, but it doesn't" % highlight(_args.static_root))
                sys.exit(1)

            if _args.remove_static:
                print_info("removing static artifacts in %s" % highlight(_args.static_root))
                shutil.rmtree(_args.static_root)

        print_info("Creating bundle tarball of %s in %s" % (highlight(_args.build_path), highlight(_args.outfile),))
        _create_targzip(_args.outfile, _args.build_path, _args.bundle_relative)

    def pack(self, args: argparse.Namespace):
        pass


packer_class = TarGzPacker
