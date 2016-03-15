#!/usr/bin/python -u
# -* coding: utf-8 *-

import gopythongo.main
from configargparse import ArgParser as ArgumentParser


def get_parser():
    parser = ArgumentParser(description="",
                            fromfile_prefix_chars="@",
                            default_config_files=["./.gopythongo"],
                            add_config_file_help=False,
                            prog="gopythongo.main pack")

    parser = gopythongo.main.add_common_parameters_to_parser(parser)

    gr_deb = parser.add_argument_group("Debian .deb settings")
    gr_deb.add_argument("--package-name", dest="package_name", default=None,
                        help="The name to assign to the package (passed to fpm -n)")
    gr_deb.add_argument("--preinst", dest="preinst", default=None,
                        help="A shell script to package as the preinst script (see Debian Policy Chapter 6)")
    gr_deb.add_argument("--postinst", dest="postinst", default=None,
                        help="A shell script to package as the postinst script (see Debian Policy Chapter 6)")
    gr_deb.add_argument("--prerm", dest="prerm", default=None,
                        help="A shell script to package as the preinst script (see Debian Policy Chapter 6)")
    gr_deb.add_argument("--postrm", dest="postrm", default=None,
                        help="A shell script to package as the preinst script (see Debian Policy Chapter 6)")
    gr_deb.add_argument("--provides", dest="provides", action="append",
                        help=".deb 'Provides:' setting")
    gr_deb.add_argument("--conflicts", dest="conflicts", action="append",
                        help=".deb 'Conflicts:' setting")
    gr_deb.add_argument("--replaces", dest="replaces", action="append",
                        help=".deb 'Replaces:' setting")
    gr_deb.add_argument("--mark-config", dest="debconfig", action="append",
                        help="Marks files or folders as configuration for .deb packages. Please note that "
                             "/etc/mn-config is provided by SaltStack")
    gr_deb.add_argument("--dir", dest="dirs", action="append",
                        help="Mark a folder as owned by the package")
    gr_deb.add_argument("--depends", dest="depends", action="append",
                        help="Add a .deb dependency")
    gr_deb.add_argument("--version", dest="version", default=None,
                        help="The package version. If not specified, this script will use the latest version from "
                             "'repo'")
    gr_deb.add_argument("--epoch", dest="epoch", default=None,
                        help="The package epoch. If not specified, this script will use the lastest epoch from "
                             "'repo'")
    gr_deb.add_argument("--aptly-config", dest="aptly_config", default=None,
                        help="Path to the aptly config file to use")
    gr_deb.add_argument("--repo", dest="repo", default=None,
                        help="Name of the aptly repository to place the package in. (This must be accessible from the "
                             "pbuilder chroot to be useful.)")
