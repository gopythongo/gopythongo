# -* encoding: utf-8 *-

import argparse

from gopythongo.utils import highlight


class VersionerHelpAction(argparse.Action):
    def __init__(self,
                 option_strings,
                 dest,
                 default=None,
                 choices=None,
                 help="Show help for GoPythonGo versioners."):
        super(VersionerHelpAction, self).__init__(option_strings=option_strings, dest=dest, default=default, nargs="?",
                                                  choices=choices, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        from gopythongo.versioners import versioners
        if values in versioners.keys():
            versioners[values].print_help()
        else:
            print("Versioners\n"
                  "==========\n"
                  "\n"
                  "Versioners are responsible for two actions:\n"
                  "\n"
                  "    1. They read a version string from a source. What the source is, depends on\n"
                  "       the versioner.\n"
                  "    2. They process the version string, changing it when configured to do so\n"
                  "       and then setting the resulting version as the output version for a\n"
                  "       GoPythonGo packer.\n"
                  "\n"
                  "You specify how to read a version using %s and split it into its\n"
                  "parts using %s. The target version is then specified using\n"
                  "%s, which can be optionally modified by setting\n"
                  "%s.\n"
                  "\n"
                  "If you want more information on the available versioners and their supported\n"
                  "methods, you want to use %s.\n"
                  "\n"
                  "Version format strings\n"
                  "----------------------\n"
                  "\n"
                  "%s and %s support the following\n"
                  "placeholders:\n"
                  "\n"
                  "    %s    - identifies the major version number (2 in '5:2.3.4-1')\n"
                  "    %s    - identifies the minor version number (3 in '5:2.3.4-1')\n"
                  "    %s    - identifies the patch version number (4 in '5:2.3.4-1')\n"
                  "    %s - identifies the revision number (1 in '5:2.3.4-1')\n"
                  "\n"
                  "You can also use the following predefined version formats for both input and\n"
                  "output:\n"
                  "\n"
                  "    %s - reads a Debian version string\n"
                  "    %s - reads a SemVer version string\n"
                  "\n"
                  "Please note that while this setup is pretty flexible, it far from delivers\n"
                  "everything you could ever ask for in a version string. Instead it's completely\n"
                  "oriented towards supporting %s. While\n"
                  "also supporting package Epochs which are easy to use for pushing out new\n"
                  "development versions of packages to staging systems. If you need additional\n"
                  "flexibility, don't hesitate to write your own Versioner for GoPythonGo.\n"
                  "\n"
                  "Version actions\n"
                  "---------------\n"
                  "\n"
                  "Typically you want to read a version string and then modify it in some way. I\n"
                  "recommend that you %s, but\n"
                  "create automatically incremented version strings for development versions which\n"
                  "are automatically distributed to your staging/development systems. GoPythonGo\n"
                  "can modify version strings through %s, which supports the\n"
                  "following parameter values:\n"
                  "\n"
                  "    %s - increment the version string epoch\n"
                  "    %s - increment the version string patch level\n"
                  "    %s - increment the version string revision\n"
                  "    %s - do nothing to the version string (the default)\n"
                  "\n"
                  "The action will be performed after reading the version string and before\n"
                  "creating the new version string.\n"
                  "\n"
                  "Best practice\n"
                  "-------------\n"
                  "\n"
                  "A good start is to read the version from your Python project so you have a\n"
                  "central point where you change the version. Make sure that your development\n"
                  "model changes the version string according to SemVer when you make a new\n"
                  "release. For example when using git flow, you change the version every time\n"
                  "you create a new release branch.\n"
                  "\n"
                  "Then you just have to make sure that your packaging system will recognize the\n"
                  "automatically incremented new version string as newer than the last one. I like\n"
                  "to use the following configuration for my development branches:\n"
                  "\n"
                  "    --read-version='pymodule:myproject:__version__' \\\n"
                  "    --parse-version-format='semver' \\\n"
                  "    --version-action='increment-revision' \\\n"
                  "    --new-version-format='debian'\n"
                  "\n"
                  "This will read the __version__ attribute from the Python module myproject in\n"
                  "the current PYTHONPATH. It will parse this value as a SemVer formatted version,\n"
                  "increment the revision part and output it as a Debian-compatible version string.\n"
                  "Storing the created package in an APT repository will ensure that they are\n"
                  "picked up by apt-get update && apt-get upgrade.\n" %
                  (highlight("--read-version"), highlight("--parse-version-format"),
                   highlight("--new-version-format"), highlight("--version-action"),
                   highlight("--help-versioner=[%s]" % ", ".join(versioners.keys())),
                   highlight("--parse-version-format"), highlight("--new-version-format"),
                   highlight("%major"), highlight("%minor"), highlight("%patch"), highlight("%revision"),
                   highlight("debian"), highlight("semver"),
                   highlight("Semantic Versioning (http://semver.org/)"),
                   highlight("keep version strings constant for release versions"),
                   highlight("--version-action"), highlight("increment-epoch"),
                   highlight("increment-patch"), highlight("increment-revision"), highlight("none")))

        parser.exit()
