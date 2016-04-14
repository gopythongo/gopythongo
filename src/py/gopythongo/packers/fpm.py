#!/usr/bin/python -u
# -* encoding: utf-8 *-

import gopythongo.main
from gopythongo import utils
from gopythongo.utils import template

import tarfile
import shutil
import os
import sys


def add_args(parser):
    gr_deb = parser.add_argument_group("Debian .deb settings")
    gr_deb.add_argument("--run-fpm", dest="run_fpm", action="append",
                        help="Execute FPM (can be used multiple times). You must pass a filename to this parameter, "
                             "which specifies a file containing the command-line parameters for invoking FPM. FPM will "
                             "be invoked with the CWD set to the build folder inside the selected builder. You can use "
                             "template processing here.")

    gr_fpm = parser.add_argument_group("FPM related options and common packaging options")
    gr_fpm.add_argument("--use-fpm", dest="fpm", default="/usr/local/bin/fpm",
                        help="The full path to the fpm executable to use")
    gr_fpm.add_argument("--file-map", dest="file_map", action="append",
                        help="Install a file in any location on the target system. The format of its parameter "
                             "is the same as the FPM file map: [local relative path]=[installed absolute path/dir]. "
                             "You can specify this argument multiple times. See "
                             "https://github.com/jordansissel/fpm/wiki/Source:-dir for more information.")
    gr_fpm.add_argument("--fpm-opts", dest="fpm_opts", action="append",
                        help="Any string specified here will be directly appended to the FPM command-line when it is "
                             "invoked, allowing you to specify arbitrary extra command-line parameters. Make sure "
                             "that you use an equals sign, i.e. --pip-opt='' to avoid 'Unknown "
                             "parameter' errors! http://bugs.python.org/issue9334")

    gr_rev = parser.add_mutually_exclusive_group()
    gr_rev.add_argument("--rev", dest="revision", default=None,
                        help="use this revision number. Helpful to supply the Jenkins build number, for example.")
    gr_rev.add_argument("--timestamp-revision-base", dest="timestamp_revision", default=None,
                        help="takes a UTC Unix Epoch timestamp as a parameter. The package revision will be "
                             "calculated from the current date's timestamp (current - timestamp-revision-base).")
    gr_rev.add_argument("--timestamp-epoch-base", dest="timestamp_epoch", default=None,
                        help="takes a UTC Unix Epoch timestamp as a parameter. The package epoch will be "
                             "calculated from the current date's timestamp (current - timestamp-epoch-base).")
    gr_rev.add_argument("--increment-revision", dest="increment_revision", action="store_true",
                        help="Take the latest revision for either the latest version or the version specified by "
                             "--version and increment it by 1.")
    gr_rev.add_argument("--increment-epoch", dest="increment_epoch", action="store_true",
                        help="Take the latest epoch for this package from the repository and increment it by 1.")


def validate_args(args):
    if not os.path.exists(args.fpm) or not os.access(args.fpm, os.X_OK):
        print("error: %s does not exist, is not accessible by GoPythonGo or is not executable." % args.fpm)
        sys.exit(1)

    if args.static_outfile or args.collect_static:
        if not (args.static_outfile and args.collect_static):
            print("error: --static-out and --collect-static must be used together")
            sys.exit(1)

    if args.mode == "deb" and not args.package_name:
        print("error: --deb requires --package-name")
        sys.exit(1)

    if args.service_folders and not args.mode == "deb":
        print("error: --service-folder requires --deb")
        sys.exit(1)

    for f in _args.service_folders:
        if os.path.isabs(f):
            if not os.path.exists(f):
                print("Error: service-folder does not exist %s" % f)
                sys.exit(1)
        else:
            full = os.path.join(_args.build_path, f)
            if not os.path.exists(full):
                print("Error: service-folder does not exist %s (%s)" % (f, full,))
                sys.exit(1)

    if args.mode == "deb" and (not args.repo or not args.aptly_config) and \
            (not args.version or not args.epoch):
        print("error: You must either specify a repo and a aptly config file then --version and")
        print("       --epoch are optional.")
        print("       Or you can specify --version AND --epoch, then")
        print("       specifying a target repo is optional.")
        sys.exit(1)

    for mapping in args.file_map:
        if "=" not in mapping:
            print("error: %s does not contain '='. A mapping must be [source file]=[destination file/dir]." % mapping)
            sys.exit(1)
        if not os.path.exists(mapping.split("=")[0]):
            print("error: %s in mapping %s does not exist and can't be packaged." % (mapping.split("=")[0], mapping))

    for f in [args.preinst, args.postinst, args.prerm, args.postrm]:
        if f and not os.path.exists(f):
            print("error: %s does not exist" % f)
            sys.exit(1)


def _create_targzip(outfile, basepath, make_paths_relative=False):
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


def _collect_static():
    global _args
    envpy = utils.create_script_path(_args.build_path, 'python')
    print('Collecting static artifacts')
    if os.path.exists(_args.static_root):
        print('    %s exists.' % _args.static_root)
        if _args.fresh_static:
            shutil.rmtree(_args.static_root)

    django_admin = utils.create_script_path(_args.build_path, 'django-admin.py')
    run_dja = [envpy, django_admin, "collectstatic"]
    if _args.django_settings_module:
        run_dja.append('--settings=%s' % _args.django_settings_module)
    run_dja.append("--noinput")
    run_dja.append("--traceback")
    utils.run_process(*run_dja)


def _build_tar():
    global _args
    if _args.collect_static:
        _collect_static()

        if os.path.exists(_args.static_root):
            print("creating static tarball of %s in %s" % (_args.static_root, _args.static_outfile,))
            _create_targzip(_args.static_outfile, _args.static_root, _args.static_relative)
        else:
            print('')
            print("error: %s should now exist, but it doesn't" % _args.static_root)
            sys.exit(1)

        if _args.remove_static:
            print("removing static artifacts in %s" % _args.static_root)
            shutil.rmtree(_args.static_root)

    print('')
    print('Creating bundle tarball of %s in %s' % (_args.build_path, _args.outfile,))
    _create_targzip(_args.outfile, _args.build_path, _args.bundle_relative)


def _create_deb():
    global _args
    fpm_deb = [
        _args.fpm, "-t", "deb", "-s", "dir", "-p", _args.outfile,
        "-n", _args.package_name,
    ]
    for p in _args.provides:
        fpm_deb.append("--provides")
        fpm_deb.append(p)
    for c in _args.conflicts:
        fpm_deb.append("--conflicts")
        fpm_deb.append(c)
    for r in _args.replaces:
        fpm_deb.append("--replaces")
        fpm_deb.append(r)
    for d in _args.depends:
        fpm_deb.append("--depends")
        fpm_deb.append(d)
    for c in _args.debconfig:
        fpm_deb.append("--config-files")
        fpm_deb.append(c)
    for d in _args.dirs:
        fpm_deb.append("--directories")
        fpm_deb.append(d)

    if _args.repo and not _args.version:
        # TODO: find latest version
        pass
    elif _args.version:
        version = _args.version

    if _args.repo and not _args.epoch:
        # TODO: find latest epoch and increment by one
        pass
    elif _args.epoch:
        epoch = _args.epoch

    ctx = {
        'basedir': _args.build_path,
        'service_folders': _args.service_folders,
        'service_folders_str': " ".join(_args.service_folders),
    }

    # build package
    fpm_deb += ["-v", version, "--epoch", epoch]
    if _args.preinst:
        scriptfile = template.process_to_tempfile(_args.preinst, ctx)
        fpm_deb += ["--before-install", scriptfile]

    if _args.postinst:
        scriptfile = template.process_to_tempfile(_args.postinst, ctx)
        fpm_deb += ["--after-install", scriptfile]

    if _args.prerm:
        scriptfile = template.process_to_tempfile(_args.prerm, ctx)
        fpm_deb += ["--before-remove", scriptfile]

    if _args.postrm:
        scriptfile = template.process_to_tempfile(_args.postrm, ctx)
        fpm_deb += ["--after-remove", scriptfile]

    if _args.file_map:
        for mapping in _args.file_map:
            fpm_deb += [mapping]

    if _args.repo:
        # TODO: compare outfile and _args.repo and copy built package
        # if necessary then update repo index
        pass


def _build_deb():
    global _args
    if _args.collect_static:
        _collect_static()
        if os.path.exists(_args.static_root):
            print("creating static .deb package of %s in %s" % (_args.static_root, _args.static_outfile,))
            _create_deb(_args.static_outfile, _args.static_root)
        else:
            print('')
            print("error: %s should now exist, but it doesn't" % _args.static_root)
            sys.exit(1)

        if _args.remove_static:
            print("removing static artifacts in %s" % _args.static_root)
            shutil.rmtree(_args.static_root)

    print('Creating .deb of %s in %s' % (_args.build_path, _args.outfile,))
    _create_deb(_args.outfile, _args.build_path)


def main(args):
    validate_args(args)

    if _args.mode == "deb":
        _build_deb()
    elif _args.mode == "tar":
        _build_tar()

    print('')
    print('Cleaning up')
    shutil.rmtree(_args.build_path)
