# -* encoding: utf-8 *-
import os
import shutil
import tarfile
import argparse

from typing import Any

from gopythongo.packers import BasePacker
from gopythongo.utils import print_info, highlight, ErrorMessage


class TarGzPacker(BasePacker):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def packer_name(self) -> str:
        return u"targz"

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        pass

    def validate_args(self, args: argparse.Namespace) -> None:
        pass

    def _create_targzip(self, outfile: str, basepath: str, args: argparse.Namespace,
                        make_paths_relative: bool=False) -> None:
        """
        creates a .tar.gz of everything below basepath, making sure all
        stored paths are relative
        """
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
                if args.verbose:
                    print('adding %s as %s' % (filepath, arcname,))
                tf.add(filepath, arcname, recursive=False)
        tf.close()
        f.close()

    def _build_tar(self, args: argparse.Namespace) -> None:
        if args.collect_static:
            self._collect_static()

            if os.path.exists(args.static_root):
                print_info("creating static tarball of %s in %s" % (highlight(args.static_root),
                                                                    highlight(args.static_outfile),))
                self._create_targzip(args.static_outfile, args.static_root, args.static_relative)
            else:
                raise ErrorMessage("%s should now exist, but it doesn't" % highlight(args.static_root))

            if args.remove_static:
                print_info("removing static artifacts in %s" % highlight(args.static_root))
                shutil.rmtree(args.static_root)

        print_info("Creating bundle tarball of %s in %s" % (highlight(args.build_path), highlight(args.outfile),))
        self._create_targzip(args.outfile, args.build_path, args.bundle_relative)

    def pack(self, args: argparse.Namespace) -> None:
        pass


packer_class = TarGzPacker
