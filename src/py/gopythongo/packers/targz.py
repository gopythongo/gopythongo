# -* encoding: utf-8 *-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import configargparse

from typing import Any, List, Union, Type

from gopythongo.packers import BasePacker
from gopythongo.utils import print_info, highlight, ErrorMessage, targz
from gopythongo.utils.buildcontext import the_context, PackerArtifact


class TarGzPacker(BasePacker):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def packer_name(self) -> str:
        return "targz"

    @property
    def provides(self) -> List[str]:
        return ["targz"]

    def add_args(self, parser: configargparse.ArgumentParser) -> None:
        gp_tgz = parser.add_argument_group("Tar/Gzip Packer options")
        gp_tgz.add_argument("--targz-basename", dest="targz_basename", default=None,
                            help="Each .tar.gz created by each instance of --targz in the parameters will be named "
                                 "[basename]_[ext]-[version].tar.gz where [ext] is specified in --targz and [version] "
                                 "is retrieved from the selected Versioner")
        gp_tgz.add_argument("--targz", dest="targz", action="append", default=[],
                            help="Takes an argument in the form 'ext:path' where 'ext' is appended to the "
                                 "targz-basename and then the contents of path are stored and compressed in a .tar.gz "
                                 "archive. 'ext' is optional, but be careful to not overwrite your archives when you "
                                 "use multiple --targz arguments.")
        gp_tgz.add_argument("--targz-relative", dest="targz_relative", action="store_true", default=False,
                            help="Store relative paths in the .tar.gz archives.")

    def validate_args(self, args: configargparse.Namespace) -> None:
        if not args.targz_basename:
            raise ErrorMessage("The Tar/Gzip Packer requires an archive base name (%s)" % highlight("--targz-basename"))

        validate_fns = []  # type: List[str]
        for spec in args.targz:
            if ":" in spec:
                ext = spec.split(":", 1)[0]
                fn = "%s_%s" % (args.targz_basename, ext)
            else:
                fn = args.targz_basename

            if fn in validate_fns:
                raise ErrorMessage("Multiple --targz parameters result in the same filename '%s'." % highlight(fn))
            else:
                validate_fns.append(fn)

    def predict_future_artifacts(self, args: configargparse.Namespace) -> Union[List[str], None]:
        # TODO: right now I don't know if this implementation will turn out to be more useful than return None
        ret = []  # type: List[str]
        for spec in args.targz:
            if ":" in spec:
                ext, path = spec.split(":", 1)
                basename = "%s_%s" % (args.targz_basename, ext)
            else:
                basename = args.targz_basename

            ret.append(basename)
        return ret if len(ret) > 0 else None

    def pack(self, args: configargparse.Namespace) -> None:
        for spec in args.targz:
            if ":" in spec:
                ext, path = spec.split(":", 1)
                fn = "%s_%s-%s.tar.gz" % (args.targz_basename, ext,
                                          str(the_context.read_version.version))
            else:
                path = spec
                fn = "%s-%s.tar.gz" % (args.targz_basename, str(the_context.read_version.version))

            # TODO: find the full path for the resulting file

            print_info("Creating bundle tarball of %s in %s" % (highlight(path), highlight(fn)))
            targz.create_targzip(filename=fn, paths=[(path, path)], make_paths_relative=args.targz_relative)

            the_context.packer_artifacts.add(PackerArtifact(
                "targz",
                fn,
                {"package_name": args.targz_basename},
                self,
                self.packer_name
            ))

    def print_help(self) -> None:
        print("%s\n"
              "==============\n"
              "\n"
              "Just creates a gzipped tar archive." % highlight(".tar.gz Packer"))


packer_class = TarGzPacker  # type: Type[TarGzPacker]
