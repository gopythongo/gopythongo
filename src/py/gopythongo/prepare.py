#!/usr/bin/python -u
# -* coding: utf-8 *-
import atexit
import shutil
import tarfile
import os
import subprocess
import sys
import tempfile
import time
import jinja2

import gopythongo.main

from configargparse import ArgParser as ArgumentParser

_args = None
_tempfiles = []


def get_parser():
    parser = ArgumentParser(description="Build a Python virtualenv deployment artifact and collect "
                                        "a Django project's static content if needed. The created "
                                        "virtualenv is ready to be deployed to a server. "
                                        "This tool is designed to be used with pbuilder so it can build a virtual "
                                        "environment in the path where it will be deployed within a chroot. "
                                        "Paramters that start with '--' (eg. --mode) can "
                                        "also be set in a config file (.gopythongo) by using .ini or .yaml-style "
                                        "syntax (eg. mode=value). If a parameter is specified in more than one place, "
                                        "then command-line values override config file values which override defaults. "
                                        "More information at http://gopythongo.com/.",
                            fromfile_prefix_chars="@",
                            default_config_files=["./.gopythongo"],
                            add_config_file_help=False,
                            prog="gopythongo.main prepare")

    pos_args = parser.add_argument_group("Positional arguments")
    pos_args.add_argument("build_path",
                          help="set the location where the virtual environment will be built, this " +
                               "is IMPORTANT as it is also the location where the virtualenv must " +
                               "ALWAYS reside (i.e. the install directory. Virtualenvs are NOT relocatable" +
                               "by default! All path parameters are relative to this path.")
    pos_args.add_argument("packages", metavar="package<=>version", nargs="+",
                          help="a list of package/version specifiers. Remember to quote your " +
                               "strings as in \"Django>=1.6,<1.7\"")

    parser = gopythongo.main.add_common_parameters_to_parser(parser)

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

    gr_bundle = parser.add_argument_group("Bundle settings")
    gr_bundle.add_argument("--bundle-relative-paths", dest="bundle_relative",
                           default=False, action="store_true",
                           help="write relative paths to the resulting .tar.gz archive")
    gr_bundle.add_argument("--virtualenv-binary", dest="virtualenv_binary",
                           help="set an alternative virtualenv binary to use",
                           default="/usr/bin/virtualenv")
    gr_bundle.add_argument("--service-folder", dest="service_folders", action="append",
                           help="Add one or more service folders to be linked from /etc/service when this .deb is "
                                "being installed. The folders must exist below (i.e. relative to) the build path "
                                "after all packages have been installed.")

    gr_fpm = parser.add_argument_group("FPM related options and common packaging options")
    gr_fpm.add_argument("--fpm", dest="fpm", default="/usr/local/bin/fpm",
                        help="The full path to the fpm executable to use")
    gr_fpm.add_argument("--file-map", dest="file_map", action="append",
                        help="Install a file in any location on the target system. The format of its parameter "
                             "is the same as the FPM file map: [local relative path]=[installed absolute path/dir]. "
                             "You can specify this argument multiple times. See "
                             "https://github.com/jordansissel/fpm/wiki/Source:-dir for more information.")

    gr_django = parser.add_argument_group("Django options")
    gr_django.add_argument("--collect-static", dest="collect_static", action="store_true",
                           help="run 'django-admin.py collectstatic' inside the bundle")
    gr_django.add_argument("--static-out", dest="static_outfile",
                           help="collect static files in STATIC_OUTFILE instead of inside the " +
                                "bundle. Must be used with '--collect-static'.")
    gr_django.add_argument("--static-relative-paths", dest="static_relative",
                           default=False, action="store_true",
                           help="write relative paths to the resulting static content .tar.gz archive")
    gr_django.add_argument("--static-root", dest="static_root", default="static/",
                           help="where to collect static files from (Django's STATIC_ROOT)")
    gr_django.add_argument("--assert-static-root-empty", dest="fresh_static", action="store_true",
                           help="if set, this script will make sure that STATIC_ROOT is empty " +
                                "before running collectstatic by DELETING it (be careful!)")
    gr_django.add_argument("--keep-staticroot", dest="remove_static",
                           default=True, action="store_false",
                           help="will make sure that STATIC_ROOT is NOT removed before bundling the " +
                                "virtualenv. This way the static files may end up in the virtualenv " +
                                "bundle")
    gr_django.add_argument("--django-settings", dest="django_settings_module",
                           help="'--settings' argument to pass to django-admin.py when it is called by " +
                                "this script")

    gr_pip = parser.add_argument_group("PIP options")
    gr_pip.add_argument("--pip-opt", dest="pip_opts", action="append",
                        help="option string to pass to pip (can be used multiple times). Make sure " +
                             "that you use an equals sign, i.e. --pip-opt='' to avoid 'Unknown " +
                             "parameter' errors! http://bugs.python.org/issue9334")

    gr_setuppy = parser.add_argument_group("Additional source packages")
    gr_setuppy.add_argument("--setuppy-install", dest="setuppy_install", action="append",
                            help="after all pip commands have run, this can run 'python setup.py install' on " +
                                 "additional packages available in any filesystem path. This option can be " +
                                 "used multiple times.")

    gr_out = parser.add_argument_group('Output options')
    gr_out.add_argument("-v", "--verbose", dest="verbose", default=False, action="store_true",
                        help="more output")

    return parser


def parse_opts():
    global _args
    parser = get_parser()
    _args = parser.parse_args()

    if not os.path.exists(_args.fpm) or not os.access(_args.fpm, os.X_OK):
        print("error: %s does not exist, is not accessible by GoPythonGo or is not executable." % _args.fpm)
        sys.exit(1)

    if _args.static_outfile or _args.collect_static:
        if not (_args.static_outfile and _args.collect_static):
            print("error: --static-out and --collect-static must be used together")
            sys.exit(1)

    if _args.mode == "deb" and not _args.package_name:
        print("error: --deb requires --package-name")
        sys.exit(1)

    if _args.service_folders and not _args.mode == "deb":
        print("error: --service-folder requires --deb")
        sys.exit(1)

    if _args.mode == "deb" and (not _args.repo or not _args.aptly_config) and \
            (not _args.version or not _args.epoch):
        print("error: You must either specify a repo and a aptly config file then --version and")
        print("       --epoch are optional.")
        print("       Or you can specify --version AND --epoch, then")
        print("       specifying a target repo is optional.")
        sys.exit(1)

    for mapping in _args.file_map:
        if "=" not in mapping:
            print("error: %s does not contain '='. A mapping must be [source file]=[destination file/dir]." % mapping)
            sys.exit(1)
        if not os.path.exists(mapping.split("=")[0]):
            print("error: %s in mapping %s does not exist and can't be packaged." % (mapping.split("=")[0], mapping))

    for f in [_args.preinst, _args.postinst, _args.prerm, _args.postrm]:
        if f and not os.path.exists(f):
            print("error: %s does not exist" % f)
            sys.exit(1)


def _run_process(*args):
    print("Running %s" % str(args))
    process = subprocess.Popen(args, stdout=sys.stdout, stderr=sys.stderr)
    while process.poll() is None:
        time.sleep(1)

    if process.returncode != 0:
        print("%s exited with return code %s" % (str(args), process.returncode))
        sys.exit(process.returncode)


def _create_script_path(virtualenv_path, script_name):
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


def _cleanup_tmpfiles():
    print("Cleaning up temporary files...")
    for f in _tempfiles:
        if os.path.exists(f):
            os.unlink(f)


def _process_template(filepath, context):
    """
    renders the template in ``filepath`` using ``context`` through Jinja2. The result
    is saved into a temporary file, which will be garbage collected automatically when the
    program exits.

    :return: the full path of the temporary file containing the result
    """
    outf, ofname = tempfile.mkstemp()
    with open(filepath) as inf:
        tplstr = inf.read()
    tpl = jinja2.Template(tplstr)
    outf.write(tpl.render(context))
    outf.close()
    _tempfiles.append(outf)
    return ofname


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
    envpy = _create_script_path(_args.build_path, 'python')
    print('Collecting static artifacts')
    if os.path.exists(_args.static_root):
        print('    %s exists.' % _args.static_root)
        if _args.fresh_static:
            shutil.rmtree(_args.static_root)

    django_admin = _create_script_path(_args.build_path, 'django-admin.py')
    run_dja = [envpy, django_admin, "collectstatic"]
    if _args.django_settings_module:
        run_dja.append('--settings=%s' % _args.django_settings_module)
    run_dja.append("--noinput")
    run_dja.append("--traceback")
    _run_process(*run_dja)


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
        scriptfile = _process_template(_args.preinst, ctx)
        fpm_deb += ["--before-install", scriptfile]

    if _args.postinst:
        scriptfile = _process_template(_args.postinst, ctx)
        fpm_deb += ["--after-install", scriptfile]

    if _args.prerm:
        scriptfile = _process_template(_args.prerm, ctx)
        fpm_deb += ["--before-remove", scriptfile]

    if _args.postrm:
        scriptfile = _process_template(_args.postrm, ctx)
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


def main():
    global _args
    parse_opts()

    atexit.register(_cleanup_tmpfiles)

    print('***')

    if _args.build_deps:
        print('*** Installing apt-get dependencies')
        _run_process('/usr/bin/sudo', '/usr/bin/apt-get', *_args.build_deps)

    print('*** Creating bundle %s' % _args.outfile)
    print('Initializing virtualenv in %s' % _args.build_path)
    _run_process(_args.virtualenv_binary, _args.build_path)
    os.chdir(_args.build_path)

    print('')
    print('Installing pip packages')
    pip_binary = _create_script_path(_args.build_path, 'pip')

    run_pip = [pip_binary, "install"]
    if _args.pip_opts:
        run_pip += _args.pip_opts
    run_pip += _args.packages
    _run_process(*run_pip)

    envpy = _create_script_path(_args.build_path, 'python')
    if _args.setuppy_install:
        print('')
        print('Installing setup.py packages')
        for path in _args.setuppy_install:
            if not (os.path.exists(path) and os.path.exists(os.path.join(path, 'setup.py'))):
                print('Cannot run setup.py in %s because it does not exist' % path)
                sys.exit(1)
            os.chdir(path)
            run_spy = [envpy, 'setup.py', 'install']
            _run_process(*run_spy)

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

    print('')
    if _args.mode == "deb":
        _build_deb()
    elif _args.mode == "tar":
        _build_tar()

    print('')
    print('Cleaning up')
    shutil.rmtree(_args.build_path)

    print('DONE')


if __name__ == "__main__":
    main()
