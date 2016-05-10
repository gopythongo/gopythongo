#!/usr/bin/python -u
# -* encoding: utf-8 *-

import os
import sys
import shutil

from gopythongo.packers import BasePacker
from gopythongo.utils import template, print_error, print_info, highlight


class FPMPacker(BasePacker):
    def __init__(self, *args, **kwargs):
        super(FPMPacker, self).__init__(*args, **kwargs)

    @property
    def packer_name(self):
        return u"fpm"

    def add_args(self, parser):
        gr_deb = parser.add_argument_group("Debian .deb settings")
        gr_deb.add_argument("--run-fpm", dest="run_fpm", action="append", metavar="OPTS_FILE",
                            default=[],
                            help="Execute FPM (can be used multiple times). You must pass a filename to this "
                                 "parameter, which specifies a file containing the command-line parameters for "
                                 "invoking FPM (one per line). FPM will be invoked with the CWD set to the build "
                                 "folder inside the selected builder. You can use template processing here")
        gr_deb.add_argument("--package-name", dest="package_name",
                            help="The canonical package name to set using 'fpm -n'")

        gr_fpm = parser.add_argument_group("FPM related options and common packaging options")
        gr_fpm.add_argument("--use-fpm", dest="fpm", default="/usr/local/bin/fpm",
                            help="The full path to the fpm executable to use")
        gr_fpm.add_argument("--fpm-format", dest="fpm_format", choices=["deb"], default="deb",
                            help="Output package format. Only 'deb' is supported for now")
        gr_fpm.add_argument("--file-map", dest="file_map", action="append", default=[],
                            help="Install a file in any location on the target system. The format of its parameter is "
                                 "the same as the FPM file map: [local relative path]=[installed absolute path/dir]. "
                                 "You can specify this argument multiple times. See "
                                 "https://github.com/jordansissel/fpm/wiki/Source:-dir for more information")
        gr_fpm.add_argument("--fpm-opts", dest="fpm_opts", action="append",
                            help="Any string specified here will be directly appended to the FPM command-line when it "
                                 "is invoked, allowing you to specify arbitrary extra command-line parameters. Make "
                                 "sure that you use an equals sign, i.e. --pip-opt='' to avoid 'Unknown parameter' "
                                 "errors! http://bugs.python.org/issue9334")

    def validate_args(self, args):
        if not os.path.exists(args.fpm) or not os.access(args.fpm, os.X_OK):
            print_error("fpm not found in path or not executable (%s).\n"
                        "You can specify an alternative executable using %s" %
                        (args.fpm, highlight("--use-fpm")))
            sys.exit(1)

        if args.fpm_format == "deb" and not args.package_name:
            print_error("%s requires %s" % (highlight("--fpm_format=deb"), highlight("--package-name")))
            sys.exit(1)

        for mapping in args.file_map:
            if "=" not in mapping:
                print_error("%s does not contain '='.\nA mapping must be formatted as "
                            "[source file]=[destination file/dir]." % highlight(mapping))
                sys.exit(1)
            if not os.path.exists(mapping.split("=")[0]):
                print_error("%s in file mapping %s\n"
                            "does not exist and can't be packaged." % (highlight(mapping.split("=")[0]),
                                                                       highlight(mapping)))

    def _create_deb(self, args):
        fpm_deb = [
            args.fpm, "-t", "deb", "-s", "dir", "-p", args.outfile,
            "-n", args.package_name,
        ]
        for p in args.provides:
            fpm_deb.append("--provides")
            fpm_deb.append(p)
        for c in args.conflicts:
            fpm_deb.append("--conflicts")
            fpm_deb.append(c)
        for r in args.replaces:
            fpm_deb.append("--replaces")
            fpm_deb.append(r)
        for d in args.depends:
            fpm_deb.append("--depends")
            fpm_deb.append(d)
        for c in args.debconfig:
            fpm_deb.append("--config-files")
            fpm_deb.append(c)
        for d in args.dirs:
            fpm_deb.append("--directories")
            fpm_deb.append(d)

        if args.repo and not args.version:
            # TODO: find latest version
            pass
        elif args.version:
            version = args.version

        if args.repo and not args.epoch:
            # TODO: find latest epoch and increment by one
            pass
        elif args.epoch:
            epoch = args.epoch

        ctx = {
            'basedir': args.build_path,
            'service_folders': args.service_folders,
            'service_folders_str': " ".join(args.service_folders),
        }

        # build package
        fpm_deb += ["-v", version, "--epoch", epoch]
        if args.preinst:
            scriptfile = template.process_to_tempfile(args.preinst, ctx)
            fpm_deb += ["--before-install", scriptfile]

        if args.postinst:
            scriptfile = template.process_to_tempfile(args.postinst, ctx)
            fpm_deb += ["--after-install", scriptfile]

        if args.prerm:
            scriptfile = template.process_to_tempfile(args.prerm, ctx)
            fpm_deb += ["--before-remove", scriptfile]

        if args.postrm:
            scriptfile = template.process_to_tempfile(args.postrm, ctx)
            fpm_deb += ["--after-remove", scriptfile]

        if args.file_map:
            for mapping in args.file_map:
                fpm_deb += [mapping]

        if args.repo:
            # TODO: compare outfile and _args.repo and copy built package
            # if necessary then update repo index
            pass

    def _build_deb(self, args):
        if args.collect_static:
            _collect_static()
            if os.path.exists(args.static_root):
                print("creating static .deb package of %s in %s" % (args.static_root, args.static_outfile,))
                _create_deb(args.static_outfile, args.static_root)
            else:
                print('')
                print("error: %s should now exist, but it doesn't" % args.static_root)
                sys.exit(1)

            if args.remove_static:
                print("removing static artifacts in %s" % args.static_root)
                shutil.rmtree(args.static_root)

        print('Creating .deb of %s in %s' % (args.build_path, args.outfile,))
        _create_deb(args.outfile, _args.build_path)

    def pack(self, args):
        validate_args(args)
        _build_deb(args)

        print_info("Cleaning up")
        shutil.rmtree(args.build_path)


packer_class = FPMPacker
